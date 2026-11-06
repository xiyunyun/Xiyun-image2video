# Xiyun Image2Video

ComfyUI 自定义节点：把 IMAGE 帧序列按真实帧率编码成 VIDEO。

解决的是「帧序列帧率和目标视频帧率不一致」的问题：例如原视频是 60fps，抽帧后接 `fps: 24` 输出，会因为帧数不对而出现慢放/快进。本节点会按时间轴重采样，保持视频时长不变。

## 功能

- 把 IMAGE 帧序列编码成 `VIDEO`，可带音轨。
- `source_fps > 0` 时按时间轴重采样（丢帧/补帧），每个输出时间点取时间上最近的源帧（等价 ffmpeg `fps` 滤镜默认的 `round=near`）。
- `source_fps = 0` 时不做重采样，直接认为帧序列已经是 `fps` 帧率。
- 自动补齐单通道/四通道图像为 RGB（灰度会转 3 通道，RGBA 取前 3 通道）。
- 编码结果会写一份临时 mp4 到 ComfyUI 的 temp 目录并复用，避免预览类节点反复请求流数据源时重复编码整段视频。

## 安装

手动安装：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/xiyunyun/Xiyun-image2video.git
```

安装后重启 ComfyUI。没有额外的 Python 依赖，只需要 ComfyUI 本身支持 `VIDEO` 输出类型（`comfy_api.latest`，即 v0.43 及以后版本）。

## 使用

节点分类：`Xiyun/视频`
节点名称：`Xiyun 图像转视频（帧率校正）`

### 输入

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `images` | IMAGE | - | 要编码成视频的图像帧序列。 |
| `fps` | FLOAT | 24.0 | 输出视频的帧率，范围 1-240。 |
| `source_fps` | FLOAT | 0.0 | 输入帧序列的实际帧率。填 0 表示不重采样。 |
| `audio` | AUDIO | 可选 | 可选音轨，编码时按视频时长截断。 |

### 输出

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `video` | VIDEO | 编码后的视频。 |

## 示例

假设原视频 60fps、已抽成 60 帧（时长 1 秒），想输出 24fps：

- `fps = 24`
- `source_fps = 60`

输出为 24 帧、时长仍为 1 秒。若把 `source_fps` 留 0，则会按 24fps 编码 60 帧，时长变成 2.5 秒，看起来就是慢放。

## License

见 [LICENSE](LICENSE) 文件。
