import os
import glob
import copy
import pickle as pkl

import pandas as pd

from data_creator import DataCreator
from batch_generator import BatchGenerator
from config_generator import ConfigGenerator
from trainer import Trainer
from models.weather.weather_model import WeatherModel
from models.baseline.moving_avg import MovingAvg
from models.baseline.convlstm import ConvLSTM
from models.baseline.u_net import UNet


model_dispatcher = {
    'moving_avg': MovingAvg,
    'convlstm': ConvLSTM,
    'u_net': UNet,
    'weather_model': WeatherModel,
}


def train_test(experiment_params, data_params, model_params):
    global_start_date = experiment_params['global_start_date']
    global_end_date = experiment_params['global_end_date']
    stride = experiment_params['data_step']
    data_length = experiment_params['data_length']
    val_ratio = experiment_params['val_ratio']
    test_ratio = experiment_params['test_ratio']
    normalize_flag = experiment_params['normalize_flag']
    model_name = experiment_params['model']
    device = experiment_params['device']
    selected_criterion = experiment_params["selected_criterion"]

    months = pd.date_range(start=global_start_date, end=global_end_date, freq=str(1) + 'M')
    for i in range(0, len(months) - (data_length - stride), stride):
        start_date_str = '-'.join([str(months[i].year), str(months[i].month), '01'])
        start_date = pd.to_datetime(start_date_str)
        end_date = start_date + pd.DateOffset(months=data_length) - pd.DateOffset(hours=1)
        date_range_str = start_date_str + "_" + end_date.strftime("%Y-%m-%d")

        data_creator = DataCreator(start_date=start_date, end_date=end_date, **data_params)
        weather_data = data_creator.create_data()

        model_core_param = model_params[model_name]["core"]
        model_trainer_param = model_params[model_name]["trainer"]
        model_batch_gen_param = model_params[model_name]["batch_gen"]
        config = {
            "data_params": data_params,
            "experiment_params": experiment_params,
            f"{model_name}_params": model_params[model_name]
        }
        batch_generator = BatchGenerator(weather_data=weather_data,
                                         val_ratio=val_ratio,
                                         test_ratio=test_ratio,
                                         params=model_batch_gen_param,
                                         normalize_flag=normalize_flag)
        config_generator = ConfigGenerator()

        # Perform grid search to find the best parameter set for the model
        print("-*-" * 10)
        print(f"TRAINING for the {date_range_str}")
        combination_num = 0
        save_dir = os.path.join('results', model_name, 'exp_' + str(get_exp_count(model_name) + 1))
        best_val_score, best_scores, best_trainer_param, best_model = 1e6, {}, {}, None
        for trainer_param in config_generator.conf_next(input_conf=model_trainer_param):
            for core_param in config_generator.conf_next(input_conf=model_core_param):
                print("--" * 20)
                print(f"Combination {combination_num}: Training '{model_name}' for the {date_range_str}")
                print("--" * 20)

                model = model_dispatcher[model_name](device=device, **core_param)
                trainer = Trainer(device=device, **trainer_param)
                train_val_loss, train_metric, val_metric = trainer.train(model, batch_generator)

                criterion = val_metric[selected_criterion]
                if criterion < best_val_score:
                    best_val_score = train_val_loss[1]
                    best_model = copy.deepcopy(model)
                    best_trainer_param = trainer_param
                    best_scores["train"] = train_metric
                    best_scores["validation"] = val_metric
                    best_scores["train_val_loss"] = train_val_loss
                    saving_checkpoint(save_dir, best_scores, model, trainer, batch_generator, config)
                combination_num += 1

        print("-*-" * 10)
        print(f"EVALUATION  for the {date_range_str}")
        trainer = Trainer(device=device, **best_trainer_param)
        eval_loss, eval_metric = trainer.evaluate(best_model, batch_generator)
        best_scores["evaluation"] = eval_metric
        best_scores["eval_loss"] = eval_loss
        saving_checkpoint(save_dir, best_scores, model, trainer, batch_generator, config)

        print("-*-" * 10)
        print(f"TEST for the {date_range_str}")
        test_loss, test_metric = trainer.predict(model, batch_generator)
        best_scores["test"] = test_metric
        best_scores["test_loss"] = test_loss
        saving_checkpoint(save_dir, best_scores, model, trainer, batch_generator, config)

        print("-*-" * 10)
        all_scores_list = [f"{key}:\t\t{trainer.get_metric_string(metrics)}"
                           for key, metrics in best_scores.items() if "_" not in key]
        all_scores_str = "\n".join(all_scores_list)
        print(f"Experiment finished for the {date_range_str} the scores are: \n"
              f"{all_scores_str}")

        # # remove dump directory
        # shutil.rmtree(dump_file_dir)

        break


def inference(model_name, device, exp_num):
    if exp_num is None:
        raise KeyError("experiment number cannot be None")
    model, trainer, batch_generator = load_checkpoint(model_name, exp_num)

    model = model.to(device)
    if model_name in ["convlstm", "weather_model"]:
        model.device = device
        for i in range(len(model.encoder)):
            model.encoder[i].device = device
            model.decoder[i].device = device
    if model_name == "moving_avg":
        model.device = device
        model.window_in = 10
    trainer.device = device
    test_loss, test_metric = trainer.predict(model, batch_generator)

    return test_loss, test_metric


def saving_checkpoint(save_dir, scores, model, trainer, batch_generator, config):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_paths = [os.path.join(save_dir, path) for path in
                  ['scores.pkl', 'model.pkl', 'trainer.pkl', "batch_generator.pkl", "config.pkl"]]
    obj_lists = [scores, model.cpu(), trainer, batch_generator, config]
    for path, obj in zip(save_paths, obj_lists):
        with open(path, 'wb') as file:
            pkl.dump(obj, file)


def load_checkpoint(model_name, exp_num):
    def load_obj(dir_path, obj_name):
        obj_path = os.path.join(dir_path, f"{obj_name}.pkl")
        with open(obj_path, "rb") as f:
            obj = pkl.load(f)
        return obj

    exps_dir = os.path.join('results', model_name, f"exp_{exp_num}")
    model = load_obj(exps_dir, "model")
    trainer = load_obj(exps_dir, "trainer")
    batch_generator = load_obj(exps_dir, "batch_generator")

    return model, trainer, batch_generator


def get_exp_count(model_name):
    save_dir = os.path.join('results', model_name)
    num_exp_dir = len(glob.glob(os.path.join(save_dir, 'exp_*')))
    return num_exp_dir



