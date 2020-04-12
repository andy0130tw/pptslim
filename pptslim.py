import argparse
import asyncio
import mimetypes
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from functools import partial

'''
Draft:

ffmpeg -loop 1 -i dummy.jpg -t 1 -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest dummy.mp4
'''

def sizeof_fmt(num, suffix='B'):
    '''from https://stackoverflow.com/a/1094933/2281355'''
    for unit in ['','K','M','G']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'T', suffix)


async def run_subp_async(args, **kwargs):
    proc = await asyncio.create_subprocess_exec(
        *args, **kwargs,
        stdout=asyncio.subprocess.PIPE)

    try:
        print('Running command', args, ':')
        async def _read_stream(stream):
            while True:
                ln = await stream.readline()
                if not ln: break
                print(f'>>> ' + ln.decode(errors='ignore').rstrip('\n'))
        await _read_stream(proc.stdout)
        await proc.wait()
    except Exception as err:
        proc.kill()
        await proc.wait()
        if isinstance(err, asyncio.TimeoutError):
            return None
        else:
            raise


def prepare_replacing_file(zipf, entry, mime):
    '''For an entry in the zip file, produce a smaller file at path of the same
    format. Return a thunk(dest) for writing to the destination,
    None otherwise.
    '''

    # the dummy file should be generated of the correct format.
    # ffmpeg can handle this by using an appropriate extension, but who cares
    async def write_mp4(dest):
        shutil.copyfile('assets/dummy.mp4', dest)

    async def write_image(dest):
        with zipf.open(entry.filename) as src, \
             tempfile.NamedTemporaryFile() as tmp:
            shutil.copyfileobj(src, tmp)
            tmp.flush()
            await run_subp_async(['convert', tmp.name + '[0]', dest])

    async def write_png(dest):
        with zipf.open(entry.filename) as src, \
             tempfile.NamedTemporaryFile(suffix='.png') as tmp:
            shutil.copyfileobj(src, tmp)
            tmp.flush()
            await run_subp_async(
                ['pngquant', tmp.name,
                 '--speed', '1',
                 '--nofs', '-v',
                 '--output', dest])

    if entry.compress_size < 100 * 1024:  # 100k? is 100k a lot?
        return None

    if mime.startswith('video/'):
        return write_mp4
    elif mime == 'image/png':
        return write_png
    elif mime.startswith('image/'):
        return write_image
    else:
        print('!! Unknown/unsupported format [{}] for file {}, skipping...'
            .format(mime, entry.filename))
        return None


def gen_parser():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('input', help='path to input file')
    parser.add_argument('output', help='path to output file')
    return parser

async def main(args):
    tmpdir = tempfile.TemporaryDirectory()

    f = tempfile.NamedTemporaryFile(suffix='.zip')
    with open(args.input, 'rb') as finp:
        shutil.copyfileobj(finp, f)

    zipf = zipfile.ZipFile(f)
    infolist = filter(lambda x: x.filename.startswith('ppt/media/'), zipf.infolist())
    zip_changed = False

    for ent in infolist:
        entpath = Path(ent.filename)
        mime = mimetypes.types_map.get(entpath.suffix, '<<unknown>>')

        # uncomment if you are only troubled with gifs...
        # if mime.startswith('image/') and mime != 'image/gif':
        #     continue

        thunk = prepare_replacing_file(zipf, ent, mime)
        if thunk is not None:
            print('> {}, type={}, size={} ({} stored)'.format(
                ent.filename, mime,
                sizeof_fmt(ent.file_size),
                sizeof_fmt(ent.compress_size)))

            zip_changed = True
            dest_dir = Path(tmpdir.name, Path(ent.filename).parent)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / entpath.name
            await thunk(str(dest))
            new_sz = dest.stat().st_size
            print(' --> new size: {}'.format(sizeof_fmt(new_sz)))

    if zip_changed:
        print('****** Updating zip...')
        await run_subp_async(['zip', '-r', f.name, '.'], cwd=tmpdir.name)
    else:
        print('****** No file is changed!')

    zipf.close()

    # here, copyfileobj on f copies the unmodified content instead, why???
    shutil.copyfile(f.name, args.output)

    print('New size ==>', sizeof_fmt(Path(args.output).stat().st_size))

    # should clean up itself
    print('****** Cleaning up...')
    tmpdir.cleanup()


if __name__ == '__main__':
    parser = gen_parser()
    asyncio.run(main(parser.parse_args()))
