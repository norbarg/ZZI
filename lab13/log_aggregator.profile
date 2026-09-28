# Generated profile for variant 3
profile log_aggregator {

    # Explicitly denied capabilities
    deny capability sys_time,
    deny capability net_admin,
    deny capability sys_admin,

    # File access rules
    C:/dev/ZZI/lab13/app_data/config/aggregator.conf rw,
    C:/dev/ZZI/lab13/app_data/incoming/source_1.log rw,
    C:/dev/ZZI/lab13/app_data/incoming/source_2.log rw,
    C:/dev/ZZI/lab13/app_data/logs/combined.log w,
    C:/dev/ZZI/lab13/app_data/logs/service.log a,
}