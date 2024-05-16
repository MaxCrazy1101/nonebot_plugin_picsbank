from typing import Optional, TypedDict

import ujson as json
from nonebot import require
from nonebot.log import logger

from .utils import dhash, calculate_hamming_distance

require("nonebot_plugin_localstore")

from nonebot_plugin_localstore import get_data_file

PicInf = TypedDict("PicInf", {"limit": int, "hash_str": int, "return": str, "sid": str})

NULL_BANK: dict[str, list[PicInf]] = {
    "0": [],  # 全局 和 群号
}

hash_method = dhash  # 设置hash方法

DATA_PATH = get_data_file("nonebot_plugin_picsbank", "bank.json")


class PicBank:
    def __init__(self):
        if DATA_PATH.exists():
            logger.info(f"读取词库位于 {DATA_PATH}")
            with DATA_PATH.open("r", encoding="utf-8") as f:
                self.data: dict[str, list[PicInf]] = json.load(f)
        else:
            logger.info(f"创建词库位于 {DATA_PATH}")
            self.data = NULL_BANK
            self.save()

    def match(self, image_bytes: bytes, group_id: str = "0") -> str:
        """
        匹配词条
        :param group_id:
        :param image_bytes:
        :return: 首先匹配成功的消息列表
        """
        # 优先检测群内
        hash_str = hash_method(image_bytes)  # 获取图片指纹信息
        if group_id != "0":
            try:
                for pic_inf in self.data[group_id]:
                    if calculate_hamming_distance(hash_str, pic_inf["hash_str"]) < pic_inf["limit"]:
                        return pic_inf["return"]
            except KeyError:
                self.data[group_id] = []
                self.save()
        # 群内匹配失败匹配全局
        for pic_inf in self.data["0"]:
            if calculate_hamming_distance(hash_str, pic_inf["hash_str"]) < pic_inf["limit"]:
                return pic_inf["return"]
        return ""

    def save(self):
        """
        :return:
        """
        with DATA_PATH.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def set(
        self,
        image_bytes: bytes,
        return_str: str,
        group_id: str = "0",
        limit: int = 5,
        sid: str = "",
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
            for pic_detail in self.data[group_id]:
                if pic_detail["hash_str"] == hash_str:
                    pic_detail["return"] = return_str
                    if sid != "":
                        pic_detail["sid"] = sid
                    self.save()
                    return "修改成功"
        except KeyError:
            self.data[group_id] = []
            self.save()
        if sid == "":  # 默认special_key
            sid = return_str
        self.data[group_id].append({"limit": limit, "hash_str": hash_str, "return": return_str, "sid": sid})
        self.save()
        return "设置成功"

    def delete(
        self,
        image_bytes: Optional[bytes] = None,
        special_id: Optional[str] = None,
        group_id: str = "0",
    ) -> str:
        """
        删除词条
        :param special_id: 利用sid删除
        :param group_id: 为0时是全局词库 默认全局
        :param image_bytes: 触发图片bytes
        :return:
        """
        if not image_bytes and not special_id:
            return "删除时 图片和sid 参数不能同时为空"
        elif image_bytes and special_id is None:
            hash_str: int = hash_method(image_bytes)
            try:
                for pic_inf in self.data[group_id]:
                    if calculate_hamming_distance(pic_inf["hash_str"], hash_str) <= pic_inf["limit"]:
                        self.data[group_id].remove(pic_inf)
                        self.save()
                        return "删除成功"
                return "删除失败,无匹配项"  # 不存在
            except KeyError:
                self.data[group_id] = []
                self.save()
                return "删除失败,未知群组"
        else:
            try:
                for pic_inf in self.data[group_id]:
                    if pic_inf["sid"] == special_id:
                        self.data[group_id].remove(pic_inf)
                        self.save()
                        return "删除成功"
            except KeyError:
                self.data[group_id] = []
                self.save()
            return "删除失败,无匹配项"  # 不存在

    def clean(self, group_id: str = "0") -> str:
        """
        清空某个对象的词库
        :param group_id: 为'0'时是全局词库
        :return:
        """
        self.data[group_id] = []  # 直接置空
        self.save()
        return f"{group_id}词库清空成功"

    def clean_all(self):
        """
        清空所有词库
        :return:
        """
        self.data = NULL_BANK
        self.save()
        return "所有词库清空成功"


pic_bank = PicBank()
