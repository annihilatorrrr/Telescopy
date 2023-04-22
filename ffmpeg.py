import sys
import asyncio
import os
import json
import logging


async def get_video_info(input_video):
    cmd = (
        f"ffprobe -v quiet -print_format json -show_streams -show_format {input_video}"
    )
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    json_data = json.loads(stdout.decode())

    video_info = {
        "width": None,
        "height": None,
        "video_codec": None,
        "audio_codec": None,
        "framerate": None,
        "bitrate": None,
    }

    for stream in json_data["streams"]:
        if stream["codec_type"] == "video":
            video_info["width"] = stream["width"]
            video_info["height"] = stream["height"]
            video_info["video_codec"] = stream["codec_name"]
            video_info["framerate"] = stream["avg_frame_rate"]
            video_info["bitrate"] = stream["bit_rate"]

        elif stream["codec_type"] == "audio":
            video_info["audio_codec"] = stream["codec_name"]

    return video_info


async def add_image_to_video(input_video, input_image, output_video, directory, image_duration=4):
    # Get the video information
    video_info = await get_video_info(input_video)

    # Create a temporary video from the image with the same duration, codec, and settings as the original video
    temp_video = f"{directory}/temp_video.ts"
    cmd = f"ffmpeg -loop 1 -i {input_image} -c:v {video_info['video_codec']} -t {image_duration} -vf scale={video_info['width']}:{video_info['height']} -r {video_info['framerate']} -b:v {video_info['bitrate']} -pix_fmt yuv420p {temp_video}"
    process = await asyncio.create_subprocess_shell(cmd)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f'FFMPEG error temp video: {stderr.decode()} \n{stdout.decode()}')

    # Convert the input video to MPEG-TS format
    input_video_ts = f"{directory}/input_video.ts"
    cmd = f"ffmpeg -i {input_video} -c copy -bsf:v h264_mp4toannexb -f mpegts {input_video_ts}"
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    if process.returncode != 0:
        raise Exception(f'FFMPEG error convert mpeg: {stderr.decode()} \n{stdout.decode()}')

    # Concatenate the original video and the temporary video
    cmd = f'ffmpeg -i "concat:{input_video_ts}|{temp_video}" -c copy -bsf:a aac_adtstoasc {output_video}'
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    if process.returncode != 0:
        raise Exception(f'FFMPEG error concat: {stderr.decode()} \n{stdout.decode()}')

    # Remove the temporary video and input_video_ts
    os.remove(temp_video)
    os.remove(input_video_ts)

    return output_video
