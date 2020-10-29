## 介绍

在刷LeetCode的过程中时常会遇到与之前类似的题目但是却忘记解题思路的情况。[Anki](https://apps.ankiweb.net/) 是一个基于遗忘曲线的全平台记忆工具，支持Mac，Linux， Windows， iOS和Andorid平台。Anki是一个优秀的记忆工具，但是在使用需要手动制卡，这个过程非常繁琐且耗时。

> Invest some time to automate or simplify a process to save more time in the future

**本项目旨在抓取LeetCode已AC的题目，并自动生成Anki卡组帮助记忆。**

抓取的数据包括：

1. 题目标题，难度，描述。
2. 官方题解（Premium的题解需要订阅才能抓取）。
3. 用户AC的提交代码。

## 使用

首先Clone仓库并安装Python依赖
```bash
git clone https://github.com/Peng-YM/LeetCode-Anki.git
cd LeetCode-Anki
pip install -r requirements.txt
```
编辑`project.conf`，填入LeetCode的用户名和密码，其他参数可以根据需求自行修改。
```configure
[User]
username = YOUR_USER_NAME_HERE
password = YOUR_PASSWORD_HERE

[DB]
path = ./data
debug = False

[Anki]
front = ./templates/front-side
back = ./templates/back-side
css = ./templates/style.css
output = ./data/LeetCode.apkg
```

运行爬虫并输出Anki卡组到`./data/LeetCode.apkg` （由`project.conf`）。

```bash
python main.py
```

愉快使用Anki复习做过的题目吧。

## LICENSE

本项目基于GPL V3开源协议。

## Acknowledgements

本项目基于众多优秀的开源项目：

- [genanki: A Library for Generating Anki Decks](https://github.com/kerrickstaley/genanki)

- [Python Markdown: Python implementation of John Gruber's Markdown](https://github.com/Python-Markdown/markdown)
