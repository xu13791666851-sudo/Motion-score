# 移动原声带 · Motion Score

跑步、驾车或在室内运动时，移动原声带可以根据目标时长、音乐风格和一句话需求安排歌单。途中改变目标时长，正在播放的歌会继续，后面的歌曲会重新编排。结束后，可以把路线、时长和歌单保存为原声带卡片，再打开试听或复用。

| 首页 | 户外播放 |
| --- | --- |
| <img src="design-assets/hd-pages/01-home.png" alt="移动原声带首页设计稿，显示夜跑建议和开始按钮" width="240"> | <img src="design-assets/hd-pages/03-outdoor-play.png" alt="户外播放页设计稿，显示当前歌曲和行程进度" width="240"> |

## 可以体验什么

- **户外跑步和驾车**可以输入起点与终点，查看高德路线、距离和预计用时。允许定位后，手机网页可在前台记录轨迹。
- **室内运动**支持跑步机、力量训练、室内单车和拉伸。选择运动与时长后，可以生成歌单并播放。
- **歌单编排**使用 DeepSeek 理解音乐偏好，按目标时长从 24 段示例音频中选曲。模型不可用时按规则编排。
- **原声带卡片**可保存、收藏、试听和复用。发现页包含示例路线。QQ 音乐账号和联网社区尚未接入。

## 本地运行完整版

安装 Python 3.10 或更新版本。在仓库根目录把 `.env.example` 复制成 `.env`。填入自己的 `AMAP_WEB_SERVICE_KEY` 启用高德地图和路线，填入 `DEEPSEEK_API_KEY` 启用 AI 编排。

在 Windows 双击 `启动本地版.cmd`，也可以运行以下命令。

```bash
python launch.py
```

启动器会打开手机体验页。手机上的实际定位需要 HTTPS 和定位授权，且当前只在页面处于前台时记录。[本地检查说明](%E6%9C%AC%E5%9C%B0%E6%A3%80%E6%9F%A5%E8%AF%B4%E6%98%8E.md)

## 离线查看设计原型

下载并完整解压 ZIP，打开 `motion-score-prototype.html`。可以查看 14 个设计页面和页面间的跳转。[下载离线原型](https://github.com/xu13791666851-sudo/Motion-score/raw/refs/heads/main/%E7%A7%BB%E5%8A%A8%E5%8E%9F%E5%A3%B0%E5%B8%A6-%E7%A6%BB%E7%BA%BF%E5%8E%9F%E5%9E%8B.zip)

## 项目资料

- [产品需求文档](%E7%A7%BB%E5%8A%A8%E5%8E%9F%E5%A3%B0%E5%B8%A6-PRD.md)
- [开发规格](%E7%A7%BB%E5%8A%A8%E5%8E%9F%E5%A3%B0%E5%B8%A6-%E5%BC%80%E5%8F%91%E8%A7%84%E6%A0%BC.md)
- [测试记录](%E6%A3%80%E6%9F%A5%E7%BB%93%E6%9E%9C.md)
- [团队仓库与功能合并记录](https://github.com/xswdd666/Motion-score/pull/1)
