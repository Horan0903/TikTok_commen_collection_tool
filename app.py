import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import time
import asyncio
import aiohttp
import brotli
from typing import Dict, List, Optional
import random
import urllib.parse
from io import BytesIO
from openpyxl import Workbook
import thulac
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import base64
import plotly.express as px
import plotly.graph_objects as go

# 初始化 THULAC 分词器（只做一次）
thu = thulac.thulac(seg_only=True)  # seg_only=True 表示只进行分词，不进行词性标注

# 从 Douyin_TikTok_Download_API 项目复制 xbogus.py 的核心功能
class XBogus:
    def __init__(self):
        self._params = None
        self._user_agent = None
        # 直接使用 xbogus.py 中的功能
        import xbogus
        self.xbogus_module = xbogus

    def _get_x_bogus(self, params: str, user_agent: str) -> str:
        """
        生成 X-Bogus签名
        :param params: 请求参数字符串
        :param user_agent: 用户代理字符串
        :return: X-Bogus 签名
        """
        try:
            # 创建新的实例并生成名
            xbogus_instance = self.xbogus_module.XBogus(user_agent)
            _, xbogus, _ = xbogus_instance.getXBogus(params)
            return xbogus
        except Exception as e:
            st.error(f"生成 X-Bogus 签名失败: {str(e)}")
            return None

# 设置页面配置
st.set_page_config(
    page_title="抖音评论采集工具",
    page_icon="💬",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main {
        padding: 20px;
    }
    .stProgress > div > div > div > div {
        background-color: #ff4b5c;
    }
</style>
""", unsafe_allow_html=True)

class DouyinCommentScraper:
    def __init__(self):
        self.base_url = "https://www.douyin.com"
        self.api_url = "https://www.douyin.com/aweme/v1/web/comment/list/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'Cookie': ''
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.x_bogus = XBogus()

    def _get_ms_token(self):
        """生成 msToken"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=107))

    async def get_comments(self, video_id: str, cursor: int = 0) -> Dict:
        """获取视频评论数据"""
        # 生成 msToken
        ms_token = self._get_ms_token()
        
        # 构建请求参数
        params = {
            'aweme_id': video_id,
            'cursor': cursor,
            'count': 20,
            'item_type': 0,
            'insert_ids': '',
            'rcFT': '',
            'pc_client_type': 1,
            'version_code': '170400',
            'version_name': '17.4.0',
            'cookie_enabled': 'true',
            'screen_width': 1920,
            'screen_height': 1080,
            'browser_language': 'zh-CN',
            'browser_platform': 'Win32',
            'browser_name': 'Chrome',
            'browser_version': '104.0.0.0',
            'browser_online': 'true',
            'platform': 'PC',
            'downlink': '10',
            'msToken': ms_token,
            'device_platform': 'webapp',
            'aid': '6383',
            'channel': 'channel_pc_web',
            'webid': '7335414539335222835',  # 可以是固定值
        }
        
        # 生成参数字符串
        params_str = urllib.parse.urlencode(params)
        
        # 生成 X-Bogus 签名
        x_bogus = self.x_bogus._get_x_bogus(params_str, self.headers['User-Agent'])
        if x_bogus:
            params['X-Bogus'] = x_bogus
            # 更新请求头
            self.headers.update({
                'X-Bogus': x_bogus,
            })
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(
                    self.api_url,
                    params=params,
                    ssl=False,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            comments = data.get('comments', [])
                            return {
                                'comments': comments,
                                'cursor': data.get('cursor', 0),
                                'has_more': data.get('has_more', False)
                            }
                        else:
                            st.error(f"API 返回数据格式错误: {data}")
                    else:
                        st.error(f"获取评论失败: HTTP {response.status}")
                        if response.status == 403:
                            st.error("Cookie 无效或已过期，请更新 Cookie")
        except Exception as e:
            st.error(f"获取评论失败: {str(e)}")
        return {}

    async def extract_video_id(self, url: str) -> Optional[str]:
        """从分享链接中提取视频ID"""
        if not url or not url.strip():
            st.error("请输入视频链接或ID")
            return None
            
        url = url.strip()
        
        # 处理纯数字ID
        if url.isdigit() and len(url) >= 19:
            return url
            
        # 处理标准视频页面URL
        if "douyin.com/video/" in url:
            try:
                video_id = url.split("video/")[1].split("/")[0].split("?")[0]
                if video_id.isdigit():
                    return video_id
            except:
                pass

        # 处理用户页面视频URL（modal_id格式）
        if "modal_id=" in url:
            try:
                video_id = url.split("modal_id=")[1].split("&")[0]
                if video_id.isdigit():
                    return video_id
            except:
                pass

        # 处理短链接
        if "v.douyin.com" in url:
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(url, allow_redirects=True) as response:
                        if response.status == 200:
                            final_url = str(response.url)
                            if "video/" in final_url:
                                video_id = final_url.split("video/")[1].split("/")[0]
                                if video_id.isdigit():
                                    return video_id
                            elif "modal_id=" in final_url:
                                video_id = final_url.split("modal_id=")[1].split("&")[0]
                                if video_id.isdigit():
                                    return video_id
            except Exception as e:
                st.error(f"解析短链接失败: {str(e)}")
                
        return None

    def update_cookie(self, cookie: str):
        """更新 Cookie"""
        if cookie:
            self.headers['Cookie'] = cookie.strip()

    async def verify_cookie(self) -> bool:
        """验证 Cookie 是否有效"""
        try:
            # 尝试访问一个需要登录的接口
            test_url = "https://www.douyin.com/aweme/v1/web/comment/list/"
            params = {
                'device_platform': 'webapp',
                'aid': '6383',
                'count': 1
            }
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(test_url, params=params, ssl=False) as response:
                    if response.status == 200:
                        return True
                    elif response.status == 403:
                        st.error("Cookie 无效或已过期")
                        return False
                    else:
                        st.error(f"验证失败: HTTP {response.status}")
                        return False
        except Exception as e:
            st.error(f"验证过程出错: {str(e)}")
            return False

def format_timestamp(timestamp: int) -> str:
    """将时间戳换为可读格式"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# 添加一个新的函数用于生成评论概况
def generate_comments_summary(comments_data: list) -> dict:
    """生成评论数据概况"""
    total_comments = len(comments_data)
    total_likes = sum(comment["点赞数"] for comment in comments_data)
    total_replies = sum(comment["回复数"] for comment in comments_data)
    
    # 计算平均值
    avg_likes = total_likes / total_comments if total_comments > 0 else 0
    avg_replies = total_replies / total_comments if total_comments > 0 else 0
    
    # 获取最早和最新评论时间
    if total_comments > 0:
        comment_times = [datetime.strptime(comment["发布时间"], '%Y-%m-%d %H:%M:%S') 
                        for comment in comments_data]
        earliest_comment = min(comment_times).strftime('%Y-%m-%d %H:%M:%S')
        latest_comment = max(comment_times).strftime('%Y-%m-%d %H:%M:%S')
    else:
        earliest_comment = "无"
        latest_comment = "无"
    
    return {
        "总评论数": total_comments,
        "总点赞数": total_likes,
        "总回复数": total_replies,
        "平均点赞数": round(avg_likes, 2),
        "平均回复数": round(avg_replies, 2),
        "最早评论时间": earliest_comment,
        "最新评论时间": latest_comment
    }

# 添加词云生成函数
def generate_wordcloud(comments_data: list) -> go.Figure:
    """生成评论词云图，返回plotly图对象"""
    # 合并所有评论文本
    text = ' '.join([comment['评论内容'] for comment in comments_data])
    
    # 使用 THULAC 进行分词
    words = []
    text_cut = thu.cut(text, text=True)
    words = text_cut.split()
    
    # 过滤停用词
    stop_words = {'的', '了', '和', '是', '就', '都', '而', '及', '与', '这', '那', '但', '然', '却',
                 '我', '你', '他', '她', '它', '们', '啊', '呀', '哦', '哈', '吧', '呢', '吗',
                 '在', '有', '个', '好', '来', '去', '到', '想', '要', '会', '能', '可以', '就是'}
    words = [word for word in words if word not in stop_words and len(word) > 1]
    
    # 生成词频统计
    word_freq = Counter(words)
    
    # 计算字体大小范围
    max_freq = max(word_freq.values())
    min_freq = min(word_freq.values())
    
    # 使用 plotly 生成词云
    fig = go.Figure(go.Scatter(
        x=[random.random() for _ in range(len(word_freq))],
        y=[random.random() for _ in range(len(word_freq))],
        text=list(word_freq.keys()),
        mode='text',
        textfont=dict(
            # 调整字体大小范围
            size=[20 + (freq / max_freq) * 80 for freq in word_freq.values()],  # 最小20px，最大100px
            color=[f'rgb({random.randint(50, 200)}, {random.randint(50, 200)}, {random.randint(50, 200)})' 
                  for _ in range(len(word_freq))]
        ),
        hovertemplate="词语: %{text}<br>频次: %{customdata}<extra></extra>",
        customdata=list(word_freq.values())
    ))
    
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.1]),
        title=dict(
            text="评论词云",
            x=0.5,
            y=0.95,
            font=dict(size=24)
        ),
        showlegend=False,
        hovermode='closest',
        width=800,
        height=600,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

# 添加时间趋势分析函数
def generate_time_trend(comments_data: list):
    """生成评论时间趋势图"""
    df = pd.DataFrame(comments_data)
    df['发布时间'] = pd.to_datetime(df['发布时间'])
    
    # 按小时统计评论数量
    df['小时'] = df['发布时间'].dt.floor('H')
    hourly_counts = df.groupby('小时').size().reset_index(name='评论数')
    
    # 使用plotly生成交互式图表
    fig = px.line(hourly_counts, 
                  x='小时', 
                  y='评论数',
                  title='评论时间分布',
                  labels={'小时': '时间', '评论数': '评论数'})
    
    fig.update_layout(
        xaxis_title="时间",
        yaxis_title="评论数量",
        hovermode='x unified'
    )
    
    return fig

async def main():
    # 添加侧边栏
    with st.sidebar:
        st.title("使用说明 📖")
        st.markdown("""
        ### 功能介绍
        本工具可以帮助你采集抖音视频的评论数据，支持批量导出。
        
        ### 使用步骤
        1. 输入视频链接或ID
        2. 设置需采集的评论数量
        3. 点击"开始采集"
        4. 等待采集完成下载数据
        
        ### 支持的输入格式
        - 分享链接：`https://v.douyin.com/xxx/`
        - 视频页面链接：`https://www.douyin.com/video/7123456789`
        - 用户页面视频链接：`https://www.douyin.com/user/xxx?modal_id=7123456789`
        - 直接输入视频ID：`7123456789`
        
        ### 注意事项
        - 采集速度受网络状况影响
        - 部分视频可能无法获取全评论
        - 请合理使用，避免频繁请求
        """)
        
        # 添加分割线
        st.markdown("---")
        
        # 添加版本信息
        st.markdown("### 版本信息")
        st.text("当前版本：v1.0.0")
        
        # 添加问题反馈区域
        st.markdown("### 问题反馈")
        if st.button("报告问题"):
            st.markdown("""
            如遇到以下问题
            1. 无法提取视频ID
            2. 评论获取失败
            3. 其他功能异常
            
            请检查：
            - 输入格式是否正确
            - 网络连接是否正常
            - 视频是否可公开访问
            """)
    
    st.title("抖音评论采集工具 💬")
    
    # Cookie 设置区域
    with st.expander("Cookie 设置（必需）", expanded=True):
        st.markdown("""
        ### 如何获取 Cookie
        
        1. 安装 [Cookie Tool](https://chromewebstore.google.com/detail/cookie-tool/gfmallmkikahpafdljpnolhgbhgkheja) 浏览器插件
        2. 访问并登录 [抖音网页版](https://www.douyin.com)
        3. 点击插件图标，选择 "Get Cookie"
        4. Cookie 会自动复制到剪贴板
        5. 粘贴到下方输入框
        
        **注意：必须使用登录后的 Cookie 才能获取评论数据**
        """)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            custom_cookie = st.text_area(
                "输入你的抖音 Cookie:",
                height=100,
                help="必须填写有效的 Cookie"
            )
        with col2:
            if st.button("验证 Cookie", type="primary"):
                if not custom_cookie:
                    st.error("请先填写 Cookie")
                else:
                    # 初始化评论采集器并验证 Cookie
                    scraper = DouyinCommentScraper()
                    scraper.update_cookie(custom_cookie.strip())
                    
                    # 使用同步方式验证
                    async def verify_cookie_async():
                        with st.spinner("正在验证 Cookie..."):
                            is_valid = await scraper.verify_cookie()
                            if is_valid:
                                st.success("Cookie 验证成功！")
                                st.session_state.cookie_verified = True
                                st.session_state.verified_cookie = custom_cookie.strip()
                            else:
                                st.session_state.cookie_verified = False
                    
                    # 使用 st.rerun() 来处理异步操作
                    st.session_state.verify_task = verify_cookie_async
                    st.rerun()
    
    # 检查 Cookie 状态
    if not custom_cookie:
        st.warning("请先填写 Cookie")
        return
    
    # 初始化评论采集器
    scraper = DouyinCommentScraper()
    
    # 使用验证过的 Cookie
    if hasattr(st.session_state, 'cookie_verified') and st.session_state.cookie_verified:
        scraper.update_cookie(st.session_state.verified_cookie)
    else:
        scraper.update_cookie(custom_cookie.strip())
    
    # 输入区域
    with st.form("input_form"):
        video_url = st.text_input(
            "请输入抖音视频链接或视频ID:", 
            placeholder="支持分享链接、视频页面链接、用户页面视频链接或直接输入视频ID"
        )
        st.caption("支持的输入格式：\n"
                   "1. 分享链接：https://v.douyin.com/xxx/\n"
                   "2. 视频页面链接：https://www.douyin.com/video/7123456789\n"
                   "3. 用户页面视频链接：https://www.douyin.com/user/xxx?modal_id=7123456789\n"
                   "4. 直接输入视频ID：7123456789")
        submit_button = st.form_submit_button("开始采集")

    if submit_button and video_url:
        with st.spinner("正在提取视频ID..."):
            video_id = await scraper.extract_video_id(video_url)
            
        if not video_id:
            st.error("无法提取视频ID，请检查链接是否正确")
            return
            
        comments_data = []
        cursor = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_comments = None
        
        while True:
            status_text.text(f"正在采集评论... (已获取 {len(comments_data)} 条评论)")
            
            response = await scraper.get_comments(video_id, cursor)
            if not response or "comments" not in response:
                break
                
            comments = response.get("comments", [])
            if not comments:
                break
                
            # 更新总评论数（如果可用）
            if total_comments is None and "total" in response:
                total_comments = response["total"]
                
            for comment in comments:
                comments_data.append({
                    "用户昵称": comment.get("user", {}).get("nickname", ""),
                    "评论内容": comment.get("text", ""),
                    "发布时间": format_timestamp(comment.get("create_time", 0)),
                    "点赞数": comment.get("digg_count", 0),
                    "回复数": comment.get("reply_comment_total", 0)
                })
                
            # 更新进度条
            if total_comments:
                progress = min(len(comments_data) / total_comments, 1.0)
            else:
                progress = 0.99  # 如果无法获取总数，显示持续进行中
            progress_bar.progress(progress)
            
            cursor = response.get("cursor", 0)
            if not cursor:
                break
                
            # 增加随机延时时间
            delay = random.uniform(1.5, 3.0)
            await asyncio.sleep(delay)
            
        status_text.text(f"采集完成! 共获取 {len(comments_data)} 条评论")
        
        if comments_data:
            # 显示评论概况
            st.subheader("📊 评论概况")
            summary = generate_comments_summary(comments_data)
            
            # 使用列布局显示概况
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总评论数", summary["总评论数"])
                st.metric("总点赞数", summary["总点赞数"])
            with col2:
                st.metric("平均点赞数", summary["平均点赞数"])
                st.metric("平均回复数", summary["平均回复数"])
            with col3:
                st.metric("总回复数", summary["总回复数"])
            
            # 显示时间范围
            st.text(f"评论时间范围: {summary['最早评论时间']} 至 {summary['最新评论时间']}")
            
            # 添加时间趋势图
            st.subheader("📈 评论时间趋势")
            time_trend_fig = generate_time_trend(comments_data)
            st.plotly_chart(time_trend_fig, use_container_width=True)
            
            # 添加词云图
            st.subheader("☁️ 评论词云")
            wordcloud_fig = generate_wordcloud(comments_data)
            
            # 显示词云图
            st.plotly_chart(wordcloud_fig, use_container_width=True)
            
            # 显示评论数据表格
            st.subheader("📝 评论详情")
            df = pd.DataFrame(comments_data)
            st.dataframe(df)
            
            # 导出功能
            st.subheader("💾 导出数据")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # CSV导出
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="下载CSV文件",
                    data=csv,
                    file_name=f"douyin_comments_{video_id}.csv",
                    mime="text/csv"
                )
                
            with col2:
                # JSON导出
                json_str = json.dumps(comments_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="下载JSON文件",
                    data=json_str,
                    file_name=f"douyin_comments_{video_id}.json",
                    mime="application/json"
                )
                
            with col3:
                # Excel导出
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    # 写入评论数据
                    df.to_excel(writer, sheet_name='评论数据', index=False)
                    
                    # 写入数据概况
                    summary_df = pd.DataFrame([summary])
                    summary_df.to_excel(writer, sheet_name='数据概况', index=False)
                
                excel_buffer.seek(0)
                st.download_button(
                    label="下载Excel文件",
                    data=excel_buffer,
                    file_name=f"douyin_comments_{video_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    # 在主程序开始时检查是否需要执行验证任务
    if hasattr(st.session_state, 'verify_task'):
        verify_task = st.session_state.verify_task
        del st.session_state.verify_task
        await verify_task()

if __name__ == "__main__":
    asyncio.run(main())
