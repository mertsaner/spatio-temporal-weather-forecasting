from experimenter import train_test, inference_on_test, get_exp_count


def run(run_params, experiment_type="train_test", infer_params=None):
    if experiment_type == "train_test":
        train_test(experiment_params=run_params["experiment_params"],
                   data_params=run_params["data_params"],
                   model_params=run_params["model_params"])
    elif experiment_type == "inference":
        inference_on_test(device=run_params["experiment_params"]["device"], **infer_params)
    else:
        raise KeyError("Wrong experiment_type, it can be either 'train_tester' or 'inference'")


def run_weatherbenc():
    from configs.weatherbench_config import experiment_params, data_params, model_params

    run_params = {
        "model_params": model_params,
        "experiment_params": experiment_params,
        "data_params": data_params
    }
    # perform train test
    run(run_params, experiment_type="train_test")

    # perform inference on test
    model_name = "weather_model"
    inference_params = {
        "model_name": model_name,
        "start_date_str": "01-01-2017",
        "end_date_str": "01-01-2018",
        "test_data_folder": "data/test_data",
        "exp_num": get_exp_count(model_name),  # get the last experiment
        # exp_number = 10  # or set it by yourself
    }
    run(run_params, experiment_type="inference", infer_params=inference_params)


if __name__ == '__main__':
    # perform experiments on weatherbench
    run_weatherbenc()

