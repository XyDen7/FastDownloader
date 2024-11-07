#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import os.path as osp
import re
import shutil
import sys
import tempfile
import requests
import six
from concurrent.futures import ThreadPoolExecutor
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from rich.console import Console
from colorama import Fore, init

os.system('clear')
init()
CHUNK_SIZE = 512 * 1024
console = Console()
DOWNLOAD_DIR = '/storage/emulated/0/Download'  # Menyimpan file di folder Downloads Android
logo = f"""{Fore.BLUE}
╔═══╗─────╔╗╔═══╗──────────╔╗────────╔╗
║╔══╝────╔╝╚╬╗╔╗║──────────║║────────║║
║╚══╦══╦═╩╗╔╝║║║╠══╦╗╔╗╔╦═╗║║╔══╦══╦═╝╠══╦═╗
║╔══╣╔╗║══╣║─║║║║╔╗║╚╝╚╝║╔╗╣║║╔╗║╔╗║╔╗║║═╣╔╝
║║──║╔╗╠══║╚╦╝╚╝║╚╝╠╗╔╗╔╣║║║╚╣╚╝║╔╗║╚╝║║═╣║
╚╝──╚╝╚╩══╩═╩═══╩══╝╚╝╚╝╚╝╚╩═╩══╩╝╚╩══╩══╩╝
{Fore.GREEN}Author: XyDen
{Fore.RED}Note:
Tools ini berfungsi untuk mendownload file dari mediafire 
dan menyimpannya di /storage/emulated/0/Download 
dan memakai fitur Paralel Downloading agar lebih cepat 
untuk mendownloadnya.
"""
def extractDownloadLink(contents):
    for line in contents.splitlines():
        m = re.search(r'href="((http|https)://download[^"]+)', line)
        if m:
            return m.groups()[0]

def download_chunk(url, start, end, sess):
    headers = {"Range": f"bytes={start}-{end}"}
    res = sess.get(url, headers=headers, stream=True)
    return res.content

def download(url, output=None, quiet=False, num_threads=8):
    url_origin = url
    sess = requests.session()
    sess.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.178 Safari/537.36"
    }

    while True:
        res = sess.get(url, stream=True)
        if 'Content-Disposition' in res.headers:
            break
        url = extractDownloadLink(res.text)
        if url is None:
            console.print(f"[bold red]Permission denied:[/bold red] {url_origin}")
            console.print("[bold yellow]Maybe you need to change permission over 'Anyone with the link'?[/bold yellow]")
            return

    if output is None:
        m = re.search('filename="(.*)"', res.headers['Content-Disposition'])
        output = m.groups()[0]
        output = output.encode('iso8859').decode('utf-8')

    output_is_path = isinstance(output, six.string_types)

    if output_is_path:
        output = osp.join(DOWNLOAD_DIR, output)

    total_size = int(res.headers.get('Content-Length', 0))
    chunk_ranges = [(i, min(i + CHUNK_SIZE - 1, total_size - 1)) for i in range(0, total_size, CHUNK_SIZE)]

    if not quiet:
        console.print(f"[bold green]Starting download...[/bold green]")
        console.print(f"[bold blue]From:[/bold blue] {url_origin}")
        console.print(f"[bold blue]Thread:[/bold blue] {num_threads}")
        console.print(f"[bold blue]To:[/bold blue] {output}")

    with Progress("[progress.description]{task.description}", BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%", TimeRemainingColumn()) as progress:
        download_task = progress.add_task("Downloading", total=total_size)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(download_chunk, url, start, end, sess) for start, end in chunk_ranges]
            chunks = []
            for future in futures:
                chunk = future.result()
                chunks.append(chunk)
                progress.update(download_task, advance=len(chunk))

    if output_is_path:
        tmp_file = tempfile.mktemp(suffix=tempfile.template, prefix=osp.basename(output), dir=osp.dirname(output))
        with open(tmp_file, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)
        shutil.move(tmp_file, output)
    else:
        for chunk in chunks:
            output.write(chunk)

    console.print(f"[bold green]Download completed![/bold green] Saved to {output}")
    return output

def main():
    print(logo)
    console.print("[bold cyan]Masukkan URL file yang ingin diunduh:[/bold cyan]")
    url = input("> ").strip()

    console.print("[bold cyan]Masukkan jumlah thread yang ingin digunakan (contoh: 8):[/bold cyan]")
    num_threads = input("> ").strip()
    while not num_threads.isdigit() or int(num_threads) <= 0:
        console.print("[bold red]Harap masukkan angka positif yang valid untuk jumlah thread.[/bold red]")
        num_threads = input("> ").strip()

    num_threads = int(num_threads)

    console.print("[bold cyan]Apakah Anda ingin menyimpan dengan nama khusus? (Y/N)[/bold cyan]")
    use_output = input("> ").strip().upper()

    output = None
    if use_output == 'Y':
        console.print("[bold cyan]Masukkan nama file output:[/bold cyan]")
        output = input("> ").strip()

    download(url, output=output, quiet=False, num_threads=num_threads)

if __name__ == "__main__":
    main()
