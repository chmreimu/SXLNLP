import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import crc

"""

基于pytorch框架编写模型训练
实现一个按首字母进行分类的任务
规律：x是一个随机单词，y是单词的分类(首字母分类)，根据x单词首字母判断出x的分类y

"""
class TxtClassifyModel(nn.Module):
    def __init__(self, batch_size):
        super(TxtClassifyModel, self).__init__()
        self.conv = nn.Conv1d(batch_size, batch_size, 1)
        self.layer1 = nn.Linear(1, 26)
        self.layer2 = nn.Linear(26, 26)
        self.batchnorm = nn.BatchNorm1d(26)
        self.dropout = nn.Dropout(0.4)
        self.activation = nn.functional.relu   # 激活函数采用relu
        self.loss = nn.functional.cross_entropy  # loss函数采用交叉熵

    def forward(self, x, y = None):
        x = self.layer1(x)
        x = self.batchnorm(x)
        x = self.activation(x)
        x = self.conv(x)
        x = self.batchnorm(x)
        x = self.activation(x)
        x = self.layer2(x)
        x = self.batchnorm(x)
        x = self.activation(x)
        x = self.dropout(x)
        if y is not None:
            return self.loss(x, y)
        return x  # 进行预测，返回26维度的概率向量

# 生成随机字符
def build_simple():
    return chr(np.random.randint(0, 26) + ord('a'))

# 生成随机单词
def build_word(word_len):
    x = []
    for i in range(word_len):
        x.append(build_simple())
    x = ''.join(x)
    return x, ord(x[0]) - ord('a')

# 将单词转换为唯一crc标签
def build_crc_label(word):
    caculate = crc.Calculator(crc.Crc8.CCITT)
    return [caculate.checksum(word.encode())]

# 生成随机单词列表
def build_words(total_words_num, word_dim):
    words = []
    crclabels = []
    labels = []
    for i in range(total_words_num):
        word, label = build_word(np.random.randint(1, word_dim))
        words.append(word)
        crclabels.append(build_crc_label(word))
        labels.append(label)
    return words, crclabels, labels

# 测试代码
# 用来测试每轮模型的准确率
def evaluate(model, sample_size, word_dim):
    model.eval()

    words, crclabels, labels = build_words(sample_size, word_dim)
    correct, wrong = 0, 0

    with torch.no_grad():
        pred = model(torch.FloatTensor(crclabels))   # 模型预测
        for p, t in zip(pred, labels):
            if np.max(p.numpy()) == t:    # 预测标签与真实标签相同，预测正确
                correct += 1
            else:
                wrong += 1
    print("正确预测个数：%d, 正确率：%f" % (correct, correct / (correct + wrong)))
    return correct / (correct + wrong)

def main():
    # 配置参数
    word_dim = 10    # 单词最大长度
    epoch_num = 500  # 训练轮数
    batch_size = 25   # 每次训练样本个数
    train_sample = 5000  # 每轮训练总共训练的样本总数
    learning_rate = 0.001  # 学习率
    # 建立模型
    model = TxtClassifyModel(batch_size)
    # 选择优化器
    optim = torch.optim.Adam(model.parameters(), lr=learning_rate)
    log = []
    # 创建训练集，正常任务是读取训练集
    words, train_crclabels, train_labels = build_words(train_sample, word_dim)
    # 训练过程
    for epoch in range(epoch_num):
        model.train()
        watch_loss = []
        for batch_index in range(train_sample // batch_size):    
            crclabels = train_crclabels[batch_index * batch_size : (batch_index + 1) * batch_size]
            labels = train_labels[batch_index * batch_size : (batch_index + 1) * batch_size]
            loss = model(torch.FloatTensor(crclabels), torch.LongTensor(labels))  # 计算loss
            loss.backward()  # 计算梯度
            optim.step()  # 更新权重
            optim.zero_grad()  # 梯度归零
            watch_loss.append(loss.item())
        print("=========\n第%d轮平均loss:%f" % (epoch + 1, np.mean(watch_loss)))
        acc = evaluate(model, batch_size, word_dim)
        log.append([acc, float(np.mean(watch_loss))])

    # 保存模型
    torch.save(model.state_dict(), "txtclassify.pt")
    # 画图
    print(log)
    plt.plot(range(len(log)), [l[0] for l in log], label="acc")  # 画acc曲线
    plt.plot(range(len(log)), [l[1] for l in log], label="loss")  # 画loss曲线
    plt.legend()
    plt.show()
    return

# 使用训练好的模型做预测
def predict(model_path, sample):
    model = TxtClassifyModel(25)
    model.load_state_dict(torch.load(model_path))  # 加载训练好的权重
    # print(model.state_dict())

    words, crclabels, labels = sample[0], sample[1], sample[2]
    model.eval()  # 测试模式
    with torch.no_grad():  # 不计算梯度
        result = model.forward(torch.FloatTensor(crclabels))  # 模型预测
        result = nn.Softmax(dim=1)(result)
    for word, pred, label in zip(words, result, labels):
        print("输入：%s, 预测类别：%c, 概率值：%f, 实际类别：%c" % (word, chr(np.argmax(pred.detach().numpy()) + ord('a')), pred[np.argmax(pred.detach().numpy())], chr(label + ord('a'))))  # 打印结果

if __name__ == '__main__':
    # main()
    sample = build_words(25, 10)
    print(sample)
    predict("txtclassify.pt", sample)
