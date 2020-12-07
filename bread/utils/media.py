import os

from django.conf import settings

import ffmpeg
from celery import shared_task


def get_audio_thumbnail(file_):
    # TODO: make this working with any storage (not only local disk)
    """Generate audio mp3 which can be played in all browsers."""
    thumbnail_name = file_.name + "_thumbnail.mp3"
    inputname = os.path.join(settings.MEDIA_ROOT, file_.name)
    outputname = os.path.join(settings.MEDIA_ROOT, thumbnail_name)
    outputurl = os.path.join(settings.MEDIA_URL, thumbnail_name)
    if not os.path.exists(outputname):
        convert_audio_task.apply_async(
            args=(inputname, outputname), result_backend=None
        )
    return outputurl


def get_video_thumbnail(file_):
    # TODO: make this working with any storage (not only local disk)
    """Generate video mp3 which can be played in all browsers."""
    thumbnail_name = file_.name + "_thumbnail.mp4"
    inputname = os.path.join(settings.MEDIA_ROOT, file_.name)
    outputname = os.path.join(settings.MEDIA_ROOT, thumbnail_name)
    outputurl = os.path.join(settings.MEDIA_URL, thumbnail_name)
    if not os.path.exists(outputname):
        convert_video_task.apply_async(
            args=(inputname, outputname), result_backend=None
        )
    return outputurl


@shared_task
def convert_audio_task(inputname, outputname):
    if os.path.exists(outputname):
        return
    if not os.path.exists(outputname):
        ffmpeg.input(inputname).filter("atrim", start=0, duration=60).output(
            outputname, format="mp3", audio_bitrate=64
        ).run()


@shared_task
def convert_video_task(inputname, outputname):
    if os.path.exists(outputname):
        return
    _in = ffmpeg.input(inputname)
    v = _in.video
    a = _in.audio
    ffmpeg.output(
        v.trim(start=0, duration=60).filter("scale", 200, -2),
        a.filter("atrim", start=0, duration=60),
        outputname,
        preset="ultrafast",
        acodec="mp3",
        audio_bitrate=64,
    ).run()
