#!/usr/bin/env python
import os
import psutil
import collections
import time
import curses
import argparse

TOP_N = 20


def get_disk_io_by_process(read_count=False, write_count=True):
    disk_io_by_process.clear()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            process = psutil.Process(proc.info['pid'])
            io_counters = process.io_counters()
            read_io = io_counters.read_count if io_counters else 0
            write_io = io_counters.write_count if io_counters else 0
            if read_count and write_count:
                io_count = read_io + write_io
            elif read_count:
                io_count = read_io
            else:
                io_count = write_io

            # 排除统计脚本自身的 PID
            if proc.info['pid'] == os.getpid():
                continue
            disk_io_by_process[proc.info['pid']] += io_count
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def show_top_processes(stdscr, disk_io_by_process, read_count=False):
    stdscr.clear()
    sorted_processes = disk_io_by_process.most_common(TOP_N)
    read_or_write = "Reads" if read_count else "Writes"
    stdscr.addstr(0, 0, f"Top {TOP_N} processes by disk {read_or_write} count:")
    stdscr.addstr(1, 0, "PID\tProcess Name\tDisk " + read_or_write)
    for i, (pid, io_count) in enumerate(sorted_processes):
        try:
            process = psutil.Process(pid)
            name = process.name()[:20].ljust(20)
            stdscr.addstr(i + 2, 0, f"{pid}\t{name}\t{io_count}")
        except psutil.NoSuchProcess:
            pass
    stdscr.refresh()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor disk read and write counts of processes.")
    parser.add_argument("-r", "--read", action="store_true", help="Monitor disk read counts")
    parser.add_argument("-w", "--write", action="store_true", help="Monitor disk write counts")
    args = parser.parse_args()

    read_count = args.read
    write_count = not args.read or args.write

    disk_io_by_process = collections.Counter()
    try:
        stdscr = curses.initscr()
        curses.curs_set(0)
        while True:
            get_disk_io_by_process(read_count=read_count, write_count=write_count)
            show_top_processes(stdscr, disk_io_by_process, read_count=read_count)
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()
