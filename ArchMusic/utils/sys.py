

import time
import psutil

from ArchMusic.misc import _boot_
from .formatters import get_readable_time


async def bot_sys_stats():
    bot_uptime = int(time.time() - _boot_)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    # Yeni eklenenler:
    net_io = psutil.net_io_counters()
    bytes_sent = net_io.bytes_sent
    bytes_recv = net_io.bytes_recv
    proc_count = len(psutil.pids())
    cpu_cores = psutil.cpu_count(logical=True)

    # Eski değerler
    UP = f"{get_readable_time((bot_uptime))}"
    CPU = f"{cpu}%"
    RAM = f"{mem}%"
    DISK = f"{disk}%"

    # Yeni değerler (okunabilir format)
    NET_SENT = f"{bytes_sent / (1024*1024):.2f} MB"
    NET_RECV = f"{bytes_recv / (1024*1024):.2f} MB"
    PROCS = f"{proc_count}"
    CORES = f"{cpu_cores}"

    return UP, CPU, RAM, DISK, NET_SENT, NET_RECV, PROCS, CORES
