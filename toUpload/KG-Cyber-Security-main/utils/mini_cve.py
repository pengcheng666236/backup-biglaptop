"""用于搜索cve中和cwe有联系的实体，缩小cve的大小"""
import pandas as pd
from tqdm import tqdm


def preprocess(df_capec):
    find_list = []
    # 用""填充空值
    df_capec = df_capec.fillna(value='')
    # 将字符串拆分成列表
    lss = df_capec["Observed Examples"].apply(split_list)
    for ls in lss:
        for l in ls:
            if "REFERENCE:" in l:
                find = l.split("REFERENCE:")[1].split(":")[0]
                if find not in find_list:
                    find_list.append(find)
    return find_list


def split_list(s: any) -> list or str:
    """按照capec文件csv格式的特点
    将开头是::的字段拆成列表

    Args:
        s (str): _description_

    Returns:
        list: _description_
        str: _description_
    """
    # 开头或结尾是::代表是列表
    if type(s) == str and ("::" == s[:2] or "::" == s[-2:]):
        return [x for x in s.strip('::').split('::') if x != '']
    else:
        return s


if __name__ == "__main__":

    with open("data/cwe.csv", 'r', encoding='utf-8') as f:
        dataf = pd.read_csv(f, index_col=False)

    find_list = preprocess(dataf)

    with open("data/cve.csv", 'r', encoding='utf-8') as f:
        data = pd.read_csv(f)
    not_list = []
    for i in tqdm(range(len(data)-1)):
        if data.iloc[i][0] not in find_list:
            not_list.append(i)
    data_new = data.drop(not_list)
    data_new.to_csv('data/cve-mini.csv')  # 将dataframe输出到csv文件中
