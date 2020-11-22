experiment_params = {
    "global_start_date": '2000-01-01',
    "global_end_date": '2008-12-31',
    "data_step": 3,
    "data_length": 12,
    "val_ratio": 0.1
}

data_params = {
    "weather_raw_dir": 'data/data_raw',
    "spatial_range": [],  # [[30, 45], [20, 50]],
    "weather_freq": 3,
    "check_files": False,
    "features": ['d', 'cc', 'z', 'pv', 'r', 'ciwc', 'clwc', 'q', 'crwc', 'cswc', 't', 'u', 'v', 'w'],
    "atm_dim": -1,
    "rebuild": False
}

batch_gen_params = {
    "input_dim": list(range(14)),
    "output_dim": 10,
    "window_in_len": 100,
    "window_out_len": 5,
    "batch_size": 8
}

trainer_params = {
    "num_epochs": 50,
    "learning_rate": 0.0001,
    "l2_reg": True,
    "clip": 5,
    "device": 'cuda',
    "early_stop_tolerance": 4
}

model_params = {
    "input_size": (61, 121),
    "window_in": 10,
    "window_out": 5,
    "num_series": 14,
    "input_attn_dim": 100,
    "temporal_attn_dim": 100,
    "encoder_params": {
        "hidden_dim": 16,
        "flow_dim": 4,
        "kernel_size": 3,
        "bias": False,
        "padding": 2,
    },
    "decoder_params": {
        "hidden_dim": 16,
        "flow_dim": 4,
        "kernel_size": 3,
        "padding": 2,
        "bias": False
    }
}
