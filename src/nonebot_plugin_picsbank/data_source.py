import ujson as json
import os
from typing import Optional
from .utils import calculate_hamming_distance, dhash
from nonebot.log import logger

NULL_BANK = {
    '0': [  # 全局 和 群号
    ],
}

hash_method = dhash  # 设置hash方法


class PicBank(object):
    def __init__(self):
        self.dir_path = os.path.abspath(os.path.join(__file__, ".."))
        self.data_path = os.path.join(self.dir_path, "bank.json")

        if os.path.exists(self.data_path):
            logger.info('读取词库位于 ' + self.data_path)
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._data = data
        else:
            logger.info('创建词库位于 ' + self.data_path)
            self._data = NULL_BANK
            self.__save()

    def match(self, image_bytes: bytes, group_id: str = '0') -> Optional[str]:
        """
        匹配词条
        :param group_id:
        :param image_bytes:
        :return: 首先匹配成功的消息列表
        """
        # 优先检测群内
        hash_str = hash_method(image_bytes)  # 获取图片指纹信息
        if group_id != '0':
            try:
                for pic_inf in self._data[group_id]:
                    if calculate_hamming_distance(hash_str, pic_inf['hash_str']) < pic_inf['limit']:
                        return pic_inf['return']
            except KeyError:
                self._data[group_id] = []
                self.__save()
        # 群内匹配失败匹配全局
        for pic_inf in self._data['0']:
            if calculate_hamming_distance(hash_str, pic_inf['hash_str']) < pic_inf['limit']:
                return pic_inf['return']
        return ''

    def __save(self):
        """
        :return:
        """
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    def set(
            self,
            image_bytes: bytes,
            return_str: str,
            group_id: str = '0',
            limit: int = 5,
            sid: str = ''
    ) -> str:
        """
        新增词条
        :param sid: 特殊的标志
        :param limit:
        :param group_id: 为0时是全局词库 默认全局
        :param image_bytes: 触发图片bytes
        :param return_str: 触发后发送的短语
        :return:
        """
        hash_str: int = hash_method(image_bytes)
        try:
            for pic_detail in self._data[group_id]:
                if pic_detail['hash_str'] == hash_str:
                    pic_detail['return'] = return_str
                    if sid != '':
                        pic_detail['sid'] = sid
                    self.__save()
                    return '修改成功'
        except KeyError:
            self._data[group_id] = []
            self.__save()
        if sid == '':  # 默认special_key
            sid = return_str
        self._data[group_id].append(
            {'limit': limit, 'hash_str': hash_str, 'return': return_str, 'sid': sid})
        self.__save()
        return '设置成功'

    def delete(
            self,
            image_bytes: Optional[bytes] = None,
            special_id: Optional[str] = None,
            group_id: str = '0'
    ) -> str:
        """
        删除词条
        :param special_id: 利用sid删除
        :param group_id: 为0时是全局词库 默认全局
        :param image_bytes: 触发图片bytes
        :return:
        """
        if not image_bytes and not special_id:
            raise "删除时 图片和sid 参数不能同时为空"
        elif special_id is None:
            hash_str: int = hash_method(image_bytes)
            try:
                for pic_inf in self._data[group_id]:
                    if pic_inf['hash_str'] == hash_str:
                        self._data[group_id].remove(pic_inf)
                        self.__save()
                        return '删除成功'
                return '删除失败,无匹配项'  # 不存在
            except KeyError:
                self._data[group_id] = []
                self.__save()
        else:
            try:
                for pic_inf in self._data[group_id]:
                    if pic_inf['sid'] == special_id:
                        self._data[group_id].remove(pic_inf)
                        self.__save()
                        return '删除成功'
            except KeyError:
                self._data[group_id] = []
                self.__save()
            return '删除失败,无匹配项'  # 不存在

    def clean(self, group_id: str = '0') -> str:
        """
        清空某个对象的词库
        :param group_id: 为'0'时是全局词库
        :return:
        """
        self._data[group_id] = []  # 直接置空
        self.__save()
        return f'{group_id}词库清空成功'

    def clean_all(self):
        """
        清空所有词库
        :return:
        """
        self._data = NULL_BANK
        self.__save()
        return "所有词库清空成功"


pic_bank = PicBank()
