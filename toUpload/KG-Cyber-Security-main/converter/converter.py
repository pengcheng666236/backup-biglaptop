import json


class Converter:
    """转换器的基类，用于继承
    """

    def __init__(self) -> None:
        """初始化函数，为空
        """
        pass

    def convert(self, file_path: str) -> json:
        """加载数据集文件，并转换成提取器所需的JSON格式

        Args:
            file_path (str): 数据集文件路径

        Returns:
            json: 提取器所需的JSON格式
        """
        return {}
