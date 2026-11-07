# Pdf To Word

这是一个对Python第三方库`pdf2docx`的图形化封装，该库将PDF文件转换为Word文档。

## 使用

下载Release中的可执行程序。双击直接运行即可，无需安装。

将PDF文件拖入程序窗口，程序会自动将其转换为Word文档，并保存在同一目录下。

## 搭建

1. 使用git clone或者解压源代码的方式将项目下载到本地。
2. `pip install -r requirements.txt`
3. 可选安装`upx`，用于压缩可执行文件产物的大小。
4. `pyinstaller p.spec`。它将单一文件`p.py`打包为单一可执行文件`dist/p.exe`。

## 说明

本项目的核心算法仅在`a.py`中，它只是包装了`pdf2docx`。`b.py`进一步编写了工作流代码，管理各个同时存在的并行转换任务，处理转换过程中的各种情况。`c.py`是基于PyQt5的图形化界面，`i.py`负责i18n。

四个文件被整合写为`o.py`。随后通过`custompyminify.py`压缩为`p.py`，再通过`pyinstaller`打包为可执行文件。
