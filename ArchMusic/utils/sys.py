import time
import psutil

from ArchMusic.misc import _boot_
from .formatters import get_readable_time


async def bot_sys_stats():
    bot_uptime = int(time.time() - _boot_)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    # Yeni eklenenler
    net_io = psutil.net_io_counters()
    bytes_sent = net_io.bytes_sent
    bytes_recv = net_io.bytes_recv
    proc_count = len(psutil.pids())
    cpu_cores = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
    ram_total = psutil.virtual_memory().total
    ram_avail = psutil.virtual_memory().available
    disk_io = psutil.disk_io_counters()
    disk_read = disk_io.read_bytes
    disk_write = disk_io.write_bytes
    boot_time = psutil.boot_time()

    # Eski değerler
    UP = f"{get_readable_time((bot_uptime))}"
    CPU = f"{cpu}%"
    RAM = f"{mem}%"
    DISK = f"{disk}%"

    # Yeni değerler (okunabilir hale getirildi)
    NET_SENT = f"{bytes_sent / (1024*1024):.2f} MB"
    NET_RECV = f"{bytes_recv / (1024*1024):.2f} MB"
    PROCS = f"{proc_count}"
    CORES = f"{cpu_cores}"
    FREQ = f"{cpu_freq:.2f} MHz"
    RAM_TOTAL = f"{ram_total / (1024**3):.2f} GB"
    RAM_AVAIL = f"{ram_avail / (1024**3):.2f} GB"
    DISK_READ = f"{disk_read / (1024*1024):.2f} MB"
    DISK_WRITE = f"{disk_write / (1024*1024):.2f} MB"
    BOOT = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_time))}"

    return (
        UP, CPU, RAM, DISK,          # eski değerler
        NET_SENT, NET_RECV,          # network
        PROCS, CORES, FREQ,          # cpu
        RAM_TOTAL, RAM_AVAIL,        # ram
        DISK_READ, DISK_WRITE,       # disk io
        BOOT                         # sistem açılış zamanı
    )
    
