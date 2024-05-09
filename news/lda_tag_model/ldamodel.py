import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_fin.settings')  # 替换 myproject.settings 为你的实际项目设置路径
django.setup()
import re
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from gensim.utils import simple_preprocess
from news.models import News

news_items = News.objects.all()

def load_stopwords(filepath):
    """
    从给定的文件路径加载停用词列表。

    参数:
    - filepath: 停用词文件的路径。

    返回:
    - 一个包含停用词的Python列表。
    """
    stopwords = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            # 移除每行的空白字符并转换为小写（可选）
            stopwords.append(line.strip().lower())
    return stopwords


# 调用函数，替换下面的'path/to/your/stopwords.txt'为你的停用词文件路径
stopwords_filepath = '../templates/stopwords.txt'
stopwords = load_stopwords(stopwords_filepath)
def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext
def preprocess(text):
    text = clean_html(text)  # 去除HTML标签
    return [word for word in simple_preprocess(text) if word not in stopwords]

# 假设 news_contents 是从 News 模型中提取的所有新闻内容的列表
news_items = News.objects.all()
news_contents = [item.content for item in news_items]
# 预处理文本数据
processed_texts = [preprocess(content) for content in news_contents]

# 创建字典
dictionary = Dictionary(processed_texts)

# 创建语料库
corpus = [dictionary.doc2bow(text) for text in processed_texts]

# 训练LDA模型
lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=10, random_state=100, update_every=1, chunksize=100, passes=10, alpha='auto', per_word_topics=True)

# 展示主题
topics = lda_model.print_topics(num_words=4)
for topic in topics:
    print(topic)

model_dir = '../models_data'
if not os.path.exists(model_dir):
    os.makedirs(model_dir)

# 保存LDA模型和字典
model_path = os.path.join(model_dir, 'lda_model.model')
dictionary_path = os.path.join(model_dir, 'lda_dictionary.dict')

lda_model.save(model_path)
dictionary.save(dictionary_path)

print(f'Model saved to: {model_path}')
print(f'Dictionary saved to: {dictionary_path}')