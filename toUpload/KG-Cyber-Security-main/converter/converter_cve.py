import json
import pandas as pd
from converter.converter import Converter


class ConverterCveToJson(Converter):
    """转换器
    将Csv格式的Cve数据集转换成便于
    提取器Extractor处理的格式
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
        with open(file_path, 'r', encoding='utf-8') as f:
            dataf = pd.read_csv(f)

        objects_dict = {}
        objects_dict['cve'] = self.preprocess(dataf).to_dict('records')

        return objects_dict

    def preprocess(self, df_capec):
        # 用""填充空值
        df_capec = df_capec.fillna(value='')
        # 将字符串拆分成列表
        for key in ["References", "Votes", "Comments"]:
            df_capec[key] = df_capec[key].apply(
                lambda x: [s for s in x.split("   |   ")])
        return df_capec
