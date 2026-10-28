"""Download the fixed challenge release and safely extract four files."""
import argparse
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request
from .data import verify_release

URL = 'https://github.com/atomityhq/forecasting-challenge/releases/download/data-v1/data-v1.tar.gz'
FILES = {'vm_cpu_readings.csv.gz','vm_metadata.csv.gz','DATA_CARD.md','SHA256SUMS'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', default='challenge_data')
    args = parser.parse_args()
    destination = Path(args.data)
    if all((destination/name).exists() for name in FILES):
        verify_release(destination)
        print('Existing release verified')
        return
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cwfc-') as tmp:
        archive = Path(tmp)/'data-v1.tar.gz'
        urllib.request.urlretrieve(URL, archive)
        with tarfile.open(archive) as source:
            members = {m.name.removeprefix('./'): m for m in source.getmembers() if m.isfile()}
            if not FILES.issubset(members):
                raise ValueError('Unexpected release layout')
            for name in sorted(FILES):
                with source.extractfile(members[name]) as inp, open(Path(tmp)/name,'wb') as out:
                    shutil.copyfileobj(inp,out)
        verify_release(tmp)
        for name in sorted(FILES):
            shutil.copyfile(Path(tmp)/name,destination/name)
    print('data-v1 downloaded and SHA-256 verified')


if __name__ == '__main__':
    main()
