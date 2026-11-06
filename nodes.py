import os
import uuid
from fractions import Fraction

import folder_paths

from comfy_api.latest import InputImpl, Types


class _ImageVideo(InputImpl.VideoFromComponents):
    # 预览类节点（如“图像对比 视频对比 GH”）会多次请求流数据源，每次都重新编码整个视频。
    # 这里在第一次请求时编码一份临时 mp4 并复用路径，避免同一批帧被反复编码。
    def __init__(self, components, bit_depth=8, color_space="sRGB"):
        super().__init__(components, bit_depth=bit_depth, color_space=color_space)
        self._stream_path = None

    def get_stream_source(self):
        if self._stream_path is None or not os.path.isfile(self._stream_path):
            path = os.path.join(folder_paths.get_temp_directory(), f"xiyun_i2v_{uuid.uuid4().hex}.mp4")
            super().save_to(path, format=Types.VideoContainer.MP4, codec=Types.VideoCodec.H264)
            self._stream_path = path
        return self._stream_path


def _rgb_only(images):
    channels = int(images.shape[-1])
    if channels == 1:
        return images.repeat(1, 1, 1, 3)
    if channels > 3:
        return images[..., :3]
    return images


def _resample_near(images, source_fps, target_fps):
    # 与 ffmpeg fps 滤镜默认的 round=near 一致：每个输出时间点取时间上最近的源帧，
    # 帧数按目标帧率变化，视频时长保持不变。
    frame_count = int(images.shape[0])
    out_count = max(1, int(round(frame_count * target_fps / source_fps)))
    indexes = [
        min(frame_count - 1, max(0, int(round(i * source_fps / target_fps))))
        for i in range(out_count)
    ]
    return images[indexes]


class XiyunImageToVideo:
    DESCRIPTION = (
        "把 IMAGE 帧序列按真实帧率编码成 VIDEO。"
        "source_fps 大于 0 时按时间轴重采样（丢帧/补帧），保持视频时长，不会慢放或快进。"
    )
    CATEGORY = "Xiyun/视频"
    FUNCTION = "encode"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "要编码成视频的图像帧序列。"}),
                "fps": ("FLOAT", {
                    "default": 24.0, "min": 1.0, "max": 240.0, "step": 0.01,
                    "tooltip": "输出视频的帧率。",
                }),
                "source_fps": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 240.0, "step": 0.01,
                    "tooltip": "输入帧序列的实际帧率，例如原视频是 60fps 就填 60，帧数会重采样成 fps 对应的数量。"
                               "0 表示不重采样，直接当作帧序列已经是 fps 帧率（已经用过 VHS force_rate 的帧填 0）。",
                }),
            },
            "optional": {
                "audio": ("AUDIO", {"tooltip": "可选音轨，编码时按视频时长截断。"}),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)

    def encode(self, images, fps, source_fps=0.0, audio=None):
        if images is None or int(images.shape[0]) == 0:
            raise ValueError("图像转视频：输入的图像帧序列为空")
        fps = float(fps)
        source_fps = float(source_fps)
        frames = _rgb_only(images)
        if source_fps > 0 and abs(source_fps - fps) > 1e-6:
            frames = _resample_near(frames, source_fps, fps)
        video = _ImageVideo(
            Types.VideoComponents(
                images=frames,
                audio=audio,
                frame_rate=Fraction(str(round(fps, 3))),
            )
        )
        return (video,)


NODE_CLASS_MAPPINGS = {
    "XiyunImageToVideo": XiyunImageToVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XiyunImageToVideo": "Xiyun 图像转视频（帧率校正）",
}
