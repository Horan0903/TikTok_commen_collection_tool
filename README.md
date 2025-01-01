# 💬 抖音评论采集工具

一个基于 Streamlit 的抖音视频评论采集工具，支持多种链接格式，提供评论数据分析和可视化功能。

## 功能特点

- 支持多种链接格式的视频评论采集
- 自动采集视频的所有评论
- 实时显示采集进度
- 提供评论数据分析和可视化
  - 评论概况统计
  - 评论时间趋势分析
  - 评论内容词云图
- 支持多种格式数据导出（CSV、JSON、Excel）

## 支持的链接格式

1. 分享链接：`https://v.douyin.com/xxx/`
2. 视频页面链接：`https://www.douyin.com/video/7123456789`
3. 用户页面视频链接：`https://www.douyin.com/user/xxx?modal_id=7123456789`
4. 直接输入视频ID：`7123456789`

## 安装说明

1. 克隆项目并进入项目目录： 
```bash
git clone https://github.com/Horan0903/TikTok_commen_collection_tool
cd 抖音评论爬取工具
```
2. 创建并激活虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate # Linux/Mac
```
或
```bash
.venv\Scripts\activate # Windows
```
3. 安装依赖：
```bash
pip install -r requirements.txt
```


## 使用说明

1. 获取抖音 Cookie：
   - 安装 [Cookie Tool](https://chromewebstore.google.com/detail/cookie-tool/gfmallmkikahpafdljpnolhgbhgkheja) 浏览器插件
   - 访问并登录 [抖音网页版](https://www.douyin.com)
   - 点击插件图标，选择 "Get Cookie"
   - 复制获取到的 Cookie

2. 运行程序：
bash
streamlit run app.py
3. 使用步骤：
   - 填入 Cookie 并验证
   - 输入视频链接或 ID
   - 点击"开始采集"
   - 等待采集完成
   - 查看数据分析结果
   - 下载所需格式的数据

## 数据分析功能

1. 评论概况：
   - 总评论数
   - 总点赞数
   - 总回复数
   - 平均点赞数
   - 平均回复数
   - 评论时间范围

2. 可视化分析：
   - 评论时间趋势图
   - 评论内容词云图

3. 数据导出格式：
   - CSV 格式
   - JSON 格式
   - Excel 格式（含数据概况）

## 注意事项

- 必须使用登录后的 Cookie 才能获取评论数据
- 采集速度受网络状况影响
- 部分视频可能无法获取全部评论
- 请合理使用，避免频繁请求

## 依赖项目

- [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API)
- [THULAC](http://thulac.thunlp.org/)

## 版本信息

当前版本：v1.0.0

## License

[MIT License](LICENSE)