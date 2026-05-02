from nicegui import ui
import random
from datetime import datetime, timedelta

# --- デザイン設定 (ブラウンベースの高級感) ---
PRIMARY_BROWN = '#5D4037'  # メイン：濃いブラウン
SECONDARY_BROWN = '#8D6E63' # サブ：明るいブラウン
BG_COLOR = '#FAF9F6'      # 背景：オフホワイト
CARD_BG = '#FFFFFF'       # カード：純白
TEXT_COLOR = '#2C1B18'    # テキスト：ほぼ黒に近い茶

# カスタムCSSの適用
ui.add_head_html(f'''
    <style>
        body {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; font-family: "Inter", "Noto Sans JP", sans-serif; }}
        .kpi-card {{ border-radius: 16px; box-shadow: 0 4px 20px rgba(62, 39, 35, 0.05); border: 1px solid rgba(141, 110, 99, 0.1); transition: transform 0.2s; }}
        .kpi-card:hover {{ transform: translateY(-2px); }}
        .sidebar-item {{ border-radius: 8px; margin: 4px 8px; transition: all 0.3s; }}
        .sidebar-item:hover {{ background-color: rgba(93, 64, 55, 0.1); }}
        .active-item {{ background-color: {PRIMARY_BROWN} !important; color: white !important; }}
        .nicegui-header {{ background-color: rgba(255, 255, 255, 0.8) !important; backdrop-filter: blur(10px); border-bottom: 1px solid rgba(0,0,0,0.05); }}
    </style>
''')

# --- ダミーデータ生成 ---
MODELS = ['ChatGPT (GPT-4o)', 'Gemini 1.5 Pro', 'Claude 3.5 Sonnet', 'Perplexity']
COMPETITORS = ['自社ブランド', '競合A社', '競合B社', '競合C社']
DATES = [(datetime.now() - timedelta(days=i)).strftime('%m/%d') for i in range(14, 0, -1)]

# --- ヘルパー関数 ---
def create_kpi_card(title, value, delta, unit="%"):
    with ui.card().classes('kpi-card p-6 bg-white'):
        ui.label(title).classes('text-sm text-gray-500 font-medium')
        with ui.row().classes('items-baseline gap-2'):
            ui.label(value).classes('text-3xl font-bold text-brown-900')
            ui.label(unit).classes('text-lg text-brown-700')
        color = 'text-green-600' if delta > 0 else 'text-red-600'
        icon = 'trending_up' if delta > 0 else 'trending_down'
        with ui.row().classes(f'items-center gap-1 {color} text-sm font-bold'):
            ui.icon(icon)
            ui.label(f'{abs(delta)}% (前月比)')

# --- 各画面の定義 ---

def show_dashboard():
    container.clear()
    with container:
        # ヘッダーエリア
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('ダッシュボード概要').classes('text-2xl font-bold')
            with ui.row().classes('gap-4'):
                ui.select(['過去30日間', '過去7日間', '本日'], value='過去30日間').classes('w-40')
                ui.select(MODELS, value=MODELS[0]).classes('w-48')

        # KPIセクション
        with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-5 gap-4 mb-8'):
            create_kpi_card('AI可視性スコア', '68.4', 4.2)
            create_kpi_card('シェア・オブ・ボイス', '32.1', -1.5)
            create_kpi_card('メンション率', '45.8', 2.1)
            create_kpi_card('引用率', '28.4', 0.8)
            create_kpi_card('回答トップ率', '12.5', 3.4)

        # グラフとインサイト
        with ui.row().classes('w-full grid grid-cols-1 lg:grid-cols-3 gap-6'):
            # 時系列推移
            with ui.card().classes('lg:col-span-2 kpi-card p-4'):
                ui.label('AI可視性スコア推移').classes('text-lg font-bold mb-4')
                ui.echart({
                    'xAxis': {'type': 'category', 'data': DATES},
                    'yAxis': {'type': 'value', 'min': 50},
                    'series': [{
                        'data': [random.randint(60, 75) for _ in range(14)],
                        'type': 'line',
                        'smooth': True,
                        'color': PRIMARY_BROWN,
                        'areaStyle': {'opacity': 0.1}
                    }],
                    'tooltip': {'trigger': 'axis'}
                }).classes('h-64')

            # インサイト
            with ui.card().classes('kpi-card p-4'):
                ui.label('今週の主要インサイト').classes('text-lg font-bold mb-4')
                with ui.column().classes('gap-4'):
                    with ui.row().classes('items-start gap-3'):
                        ui.icon('auto_awesome', color='amber').classes('text-xl')
                        ui.label('「導入しやすさ」に関するクエリで、Geminiでの推奨順位が1位に上昇しました。').classes('text-sm')
                    with ui.row().classes('items-start gap-3'):
                        ui.icon('warning', color='red').classes('text-xl')
                        ui.label('競合B社が「価格比較」クエリにおいて、新しい比較記事からの引用を急増させています。').classes('text-sm')
                    with ui.button('詳細レポートを見る').props('flat').classes('mt-4 text-brown-700'):
                        pass

def show_competitor():
    container.clear()
    with container:
        ui.label('競合比較分析').classes('text-2xl font-bold mb-6')
        
        with ui.row().classes('w-full grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8'):
            # シェア比較グラフ
            with ui.card().classes('kpi-card p-4'):
                ui.label('メンション・シェア (主要4モデル平均)').classes('text-lg font-bold mb-4')
                ui.echart({
                    'tooltip': {'trigger': 'item'},
                    'legend': {'bottom': '0'},
                    'series': [{
                        'type': 'pie',
                        'radius': ['40%', '70%'],
                        'avoidLabelOverlap': False,
                        'itemStyle': {'borderRadius': 10, 'borderColor': '#fff', 'borderWidth': 2},
                        'label': {'show': False},
                        'data': [
                            {'value': 35, 'name': '自社ブランド', 'itemStyle': {'color': PRIMARY_BROWN}},
                            {'value': 25, 'name': '競合A社', 'itemStyle': {'color': SECONDARY_BROWN}},
                            {'value': 20, 'name': '競合B社', 'itemStyle': {'color': '#D7CCC8'}},
                            {'value': 20, 'name': '競合C社', 'itemStyle': {'color': '#EFEBE9'}},
                        ]
                    }]
                }).classes('h-64')

            # スコア比較
            with ui.card().classes('kpi-card p-4'):
                ui.label('指標別ベンチマーク').classes('text-lg font-bold mb-4')
                ui.echart({
                    'dataset': {
                        'source': [
                            ['score', 'amount', 'product'],
                            [85, 85, '可視性'],
                            [72, 72, 'メンション'],
                            [65, 65, '引用シェア'],
                            [90, 90, 'ポジティブ度'],
                            [45, 45, 'トップ率']
                        ]
                    },
                    'grid': {'containLabel': True},
                    'xAxis': {'name': 'Score'},
                    'yAxis': {'type': 'category'},
                    'series': [{'type': 'bar', 'encode': {'x': 'amount', 'y': 'product'}, 'itemStyle': {'color': PRIMARY_BROWN}}]
                }).classes('h-64')

        # 比較テーブル
        columns = [
            {'name': 'brand', 'label': 'ブランド', 'field': 'brand', 'align': 'left'},
            {'name': 'visibility', 'label': '可視性スコア', 'field': 'visibility', 'sortable': True},
            {'name': 'mention', 'label': 'メンション率', 'field': 'mention'},
            {'name': 'citation', 'label': '引用シェア', 'field': 'citation'},
            {'name': 'sentiment', 'label': '推奨度(Net)', 'field': 'sentiment'},
        ]
        rows = [
            {'brand': '自社ブランド', 'visibility': 78, 'mention': '45%', 'citation': '32%', 'sentiment': '+42'},
            {'brand': '競合A社', 'visibility': 65, 'mention': '38%', 'citation': '25%', 'sentiment': '+15'},
            {'brand': '競合B社', 'visibility': 58, 'mention': '30%', 'citation': '22%', 'sentiment': '-5'},
            {'brand': '競合C社', 'visibility': 42, 'mention': '22%', 'citation': '15%', 'sentiment': '+10'},
        ]
        ui.table(columns=columns, rows=rows, row_key='brand').classes('w-full kpi-card shadow-none')

def show_intent():
    container.clear()
    with container:
        ui.label('意図クラスタ分析').classes('text-2xl font-bold mb-6')
        
        clusters = [
            {'name': '一般想起 (Generic)', 'score': 82, 'trend': '+5', 'desc': '「おすすめのSaaSは？」等の広範な質問'},
            {'name': '比較検討 (Comparison)', 'score': 64, 'trend': '-2', 'desc': '「A社とB社の違いは？」等の比較質問'},
            {'name': '価格・コスト (Pricing)', 'score': 45, 'trend': '+12', 'desc': '「料金プランは？」「コスパは？」等の質問'},
            {'name': '信頼性・実績 (Trust)', 'score': 71, 'trend': '+1', 'desc': '「導入実績は？」「セキュリティは？」等の質問'},
        ]

        with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-4 mb-8'):
            for c in clusters:
                with ui.card().classes('kpi-card p-5 cursor-pointer hover:bg-brown-50'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label(c['name']).classes('text-lg font-bold')
                        ui.badge(c['trend'], color='green' if '+' in c['trend'] else 'red')
                    ui.label(c['desc']).classes('text-sm text-gray-500 mb-4')
                    with ui.row().classes('items-center gap-2'):
                        ui.label('可視性スコア:').classes('text-xs')
                        ui.linear_progress(c['score']/100, show_value=False).classes('w-32').props('color=brown-5')
                        ui.label(f"{c['score']}").classes('font-bold')

        with ui.card().classes('w-full kpi-card p-6'):
            ui.label('選択中のクラスタ詳細: 一般想起').classes('text-xl font-bold mb-4')
            with ui.row().classes('w-full grid grid-cols-1 lg:grid-cols-2 gap-8'):
                with ui.column():
                    ui.label('代表的なプロンプト').classes('font-bold text-sm text-brown-700')
                    ui.label('・最新のマーケティング分析ツールのおすすめを教えて').classes('p-2 bg-gray-50 rounded')
                    ui.label('・B2B SaaSでAI活用が進んでいるサービスは？').classes('p-2 bg-gray-50 rounded')
                    
                    ui.label('主要引用元ドメイン').classes('font-bold text-sm text-brown-700 mt-4')
                    ui.label('1. it-review.jp (42%)').classes('text-sm')
                    ui.label('2. techcrunch.com (18%)').classes('text-sm')
                
                with ui.column().classes('p-4 bg-brown-50 rounded-xl border border-brown-100'):
                    ui.label('AIの代表的な回答傾向').classes('font-bold text-sm text-brown-800 mb-2')
                    ui.markdown('''
                    「**自社ブランド**」は、特にAI統合機能において高い評価を受けており、多くのモデルで最初に言及されます。
                    一方で、中小企業向けのプランについては言及が少なく、競合A社にシェアを譲る傾向があります。
                    ''').classes('text-sm leading-relaxed')

def show_citation():
    container.clear()
    with container:
        ui.label('引用元分析').classes('text-2xl font-bold mb-6')
        
        with ui.row().classes('w-full grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8'):
            with ui.card().classes('kpi-card p-4'):
                ui.label('引用元カテゴリ比率').classes('font-bold mb-4')
                ui.echart({
                    'series': [{'type': 'pie', 'data': [
                        {'name': 'Owned (自社)', 'value': 25},
                        {'name': 'Earned (メディア)', 'value': 55},
                        {'name': 'Third-party (SNS/掲示板)', 'value': 20}
                    ], 'itemStyle': {'color': PRIMARY_BROWN}}]
                }).classes('h-48')
            
            with ui.card().classes('lg:col-span-2 kpi-card p-4'):
                ui.label('ドメイン別引用数ランキング').classes('font-bold mb-4')
                ui.echart({
                    'xAxis': {'type': 'value'},
                    'yAxis': {'type': 'category', 'data': ['it-review.jp', 'boxil.jp', 'note.com', 'qiita.com', 'nikkei.com']},
                    'series': [{'type': 'bar', 'data': [120, 95, 80, 45, 30], 'itemStyle': {'color': SECONDARY_BROWN}}]
                }).classes('h-48')

        ui.label('高影響力URLリスト').classes('text-lg font-bold mb-4')
        columns = [
            {'name': 'url', 'label': 'URL', 'field': 'url', 'align': 'left'},
            {'name': 'type', 'label': '種別', 'field': 'type'},
            {'name': 'count', 'label': '引用回数', 'field': 'count', 'sortable': True},
            {'name': 'impact', 'label': '影響度スコア', 'field': 'impact'},
        ]
        rows = [
            {'url': 'https://www.it-review.jp/products/our-brand/reviews', 'type': 'Earned', 'count': 42, 'impact': 95},
            {'url': 'https://our-brand.com/blog/ai-strategy', 'type': 'Owned', 'count': 28, 'impact': 88},
            {'url': 'https://boxil.jp/mag/a1234/', 'type': 'Earned', 'count': 15, 'impact': 72},
        ]
        ui.table(columns=columns, rows=rows, row_key='url').classes('w-full kpi-card shadow-none')

def show_logs():
    container.clear()
    with container:
        ui.label('回答サンプル / 監査ログ').classes('text-2xl font-bold mb-6')
        
        with ui.column().classes('w-full gap-4'):
            for i in range(3):
                with ui.expansion(f"クエリ: 「次世代の分析ツール比較」 - {MODELS[i]}", icon='search').classes('w-full kpi-card bg-white'):
                    with ui.column().classes('p-4 gap-4'):
                        with ui.row().classes('w-full justify-between'):
                            ui.badge('Sentiment: Positive', color='green')
                            ui.label('取得日時: 2024-05-20 14:20').classes('text-xs text-gray-400')
                        
                        with ui.card().classes('bg-gray-50 shadow-none border-none w-full'):
                            ui.label('AIの回答本文').classes('text-xs font-bold text-gray-500')
                            ui.label('「市場にはいくつかの有力なツールがありますが、特に自社ブランドはAI機能をいち早く取り入れており、操作性に優れています。一方、競合A社は...」').classes('text-sm italic')
                        
                        with ui.row().classes('w-full grid grid-cols-4 gap-2'):
                            for label, val in [('Mention', 'Yes'), ('Rank', '#1'), ('Citation', '2件'), ('Score', '92')]:
                                with ui.column().classes('items-center p-2 bg-brown-50 rounded'):
                                    ui.label(label).classes('text-[10px] uppercase text-brown-400')
                                    ui.label(val).classes('font-bold text-brown-900')

def show_settings():
    container.clear()
    with container:
        ui.label('システム設定').classes('text-2xl font-bold mb-6')
        with ui.card().classes('w-full kpi-card p-8'):
            with ui.column().classes('w-full max-w-2xl gap-6'):
                ui.input('対象ブランド名', value='自社ブランド').classes('w-full')
                ui.textarea('競合ブランド名 (改行区切り)', value='競合A社\n競合B社\n競合C社').classes('w-full')
                with ui.row().classes('w-full gap-4'):
                    ui.select(['毎日', '毎週', 'リアルタイム'], label='実行頻度', value='毎日').classes('flex-1')
                    ui.number('スコア重み (AI露出度)', value=0.6).classes('flex-1')
                ui.label('監視対象モデル').classes('font-bold mt-4')
                with ui.row():
                    ui.checkbox('GPT-4o', value=True)
                    ui.checkbox('Gemini 1.5 Pro', value=True)
                    ui.checkbox('Claude 3.5 Sonnet', value=True)
                    ui.checkbox('Perplexity', value=True)
                ui.button('設定を保存する').props('unelevated').classes('bg-brown-700 text-white px-8 py-2 rounded-lg mt-6')

# --- メインレイアウト ---

with ui.header(elevated=False).classes('q-pa-md row items-center justify-between'):
    with ui.row().classes('items-center gap-4'):
        ui.icon('analytics', size='32px', color='brown-9')
        ui.label('LLMO Insights Pro').classes('text-xl font-bold text-brown-900')
    
    with ui.row().classes('items-center gap-6'):
        ui.label('yokoyama@toyou.co.jp').classes('text-sm text-gray-600')
        ui.avatar('person', color='brown-2', text_color='brown-9')

with ui.left_drawer(value=True).classes('bg-white border-r border-gray-100 p-0'):
    with ui.column().classes('w-full h-full justify-between pb-8'):
        with ui.column().classes('w-full gap-1 mt-4'):
            # ナビゲーション
            nav_items = [
                ('dashboard', 'ダッシュボード', show_dashboard),
                ('compare_arrows', '競合比較', show_competitor),
                ('hub', '意図クラスタ', show_intent),
                ('link', '引用元分析', show_citation),
                ('history', '回答ログ', show_logs),
                ('settings', '設定', show_settings),
            ]
            
            buttons = {}
            def navigate(name, func):
                for b in buttons.values():
                    b.classes(remove='active-item')
                buttons[name].classes(add='active-item')
                func()

            for icon, label, func in nav_items:
                buttons[label] = ui.button(on_click=lambda f=func, l=label: navigate(l, f))\
                    .props('flat no-caps align=left').classes('sidebar-item w-full py-3 px-4 text-brown-800')
                with buttons[label]:
                    with ui.row().classes('items-center gap-4'):
                        ui.icon(icon)
                        ui.label(label).classes('font-medium')

        with ui.card().classes('mx-4 p-4 bg-brown-900 text-white rounded-2xl'):
            ui.label('Pro Plan').classes('text-xs font-bold text-brown-300')
            ui.label('残りクレジット: 84%').classes('text-sm mb-2')
            ui.linear_progress(0.84).props('color=brown-3')

# コンテンツ表示エリア
container = ui.column().classes('w-full p-8 max-w-7xl mx-auto')

# 初期表示
show_dashboard()
buttons['ダッシュボード'].classes(add='active-item')

ui.run(title='LLMO Insights Pro', port=3000)