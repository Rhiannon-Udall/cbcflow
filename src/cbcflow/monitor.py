import os
from shutil import which

import configargparse

from .configuration import get_cbcflow_config
from .database import GraceDbDatabase


def generate_crondor():
    """
    Creates a periodic condor to run the monitor action.
    """
    from glue import pipeline

    parser = configargparse.ArgumentParser()
    parser.add_argument(
        "--config-file",
        default="~/.cbcflow.cfg",
        help="The cfg from which to obtain monitor configuration info",
    )
    parser.add_argument(
        "--monitor-interval",
        default=2,
        help="The interval in hours between runs of the monitoring job",
    )
    parser.add_argument(
        "--rundir",
        default=None,
        help="The directory in which to produce sub and output files",
    )
    parser.add_argument(
        "--ligo-accounting",
        default=os.environ["LIGO_ACCOUNTING"],
        help="The LIGO accounting group for the job to be tagged with",
    )
    parser.add_argument(
        "--ligo-user-name",
        default=os.environ["LIGO_USER_NAME"],
        help="The LIGO accounting user for the job to be tagged with",
    )
    args = parser.parse_args()

    if args.rundir is None:
        rundir = os.getcwd()
    else:
        rundir = args.rundir

    monitor_exe = which("monitor_run")
    monitor_job = pipeline.CondorJob(
        universe="vanilla", executable=monitor_exe, queue=1
    )
    monitor_job.set_log_file(os.path.join(rundir, "monitor.log"))
    monitor_job.set_stdout_file(os.path.join(rundir, "monitor.out"))
    monitor_job.set_stderr_file(os.path.join(rundir, "monitor.err"))
    monitor_job.add_condor_cmd("accounting_group", args.ligo_accounting)
    monitor_job.add_condor_cmd("accounting_group_user", args.ligo_user_name)
    monitor_job.add_condor_cmd("request_memory", "40 Mb")
    monitor_job.add_condor_cmd("request_disk", "10 Mb")
    monitor_job.add_condor_cmd("notification", "never")
    monitor_job.add_condor_cmd("initialdir", rundir)
    monitor_job.add_condor_cmd("get_env", "True")
    monitor_job.add_condor_cmd("on_exit_remove", "False")
    monitor_job.add_condor_cmd("cron_hour", f"* / {args.monitor_interval}")
    monitor_job.add_condor_cmd("cron_prep_time", "300")
    monitor_args = f" {os.path.expanduser(args.config_file)} "
    monitor_job.add_arg(monitor_args)
    sub_path = os.path.join(rundir, "monitor.sub")
    monitor_job.set_sub_file(sub_path)
    monitor_job.write_sub_file()

    os.system(f"condor_submit {sub_path}")


def run_monitor():
    """
    Pulls all superevents created within the past 30 days, creates metadata if necessary,
    then pushes back any changes made in this process
    """
    parser = configargparse.ArgumentParser(
        config_file_parser_class=configargparse.ConfigparserConfigFileParser
    )
    parser.add_argument(
        "cbcflowconfig",
        type=str,
        help="The .cbcflow.cfg file to use for library and service URL info",
    )
    args = parser.parse_args()

    config_values = get_cbcflow_config(args.cbcflowconfig)
    GDb = GraceDbDatabase(config_values["gracedb_service_url"])
    GDb.sync_library_gracedb(config_values["library"])
