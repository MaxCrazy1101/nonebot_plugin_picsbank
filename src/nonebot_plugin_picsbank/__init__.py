import re
from nonebot.log import logger
from nonebot.plugin import on_message, on_command
from nonebot.adapters.cqhttp import (Event, GroupMessageEvent, PrivateMessageEvent, GROUP_ADMIN, GROUP_OWNER, Bot,
                                     Message, MessageEvent, unescape)
from nonebot.typing import T_State
from .utils import get_pic_from_url, get_message_images, parse
from .data_source import pic_bank as pb
from nonebot.permission import SUPERUSER

__author__ = "Alex Newton"
__usage__ = """
    pb添加 [全局][匹配率+(64以下数字)][sid(任意特殊标记，可用于删除词条)]发[图片]答....  例:全局匹配率5sidnihao发[这是一张图片]答我爱你
    pb删除 [sid/图片] 
"""
__version__ = '0.1.2'
__plugin_name__ = "pics_bank"


async def check_img(bot: Bot, event: Event, state: T_State) -> bool:
    img_list = get_message_images(event.json())
    state['img_list'] = img_list
    return len(img_list) != 0


pics_bank = on_message(rule=check_img, priority=98)  # 优先级比word_bank略高


@pics_bank.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    msg = pb.match(await get_pic_from_url(state['img_list'][0]), str(event.group_id))
    if msg == '':
        await pics_bank.finish()
    msg = Message(unescape(
        parse(msg=msg, nickname=event.sender.card or event.sender.nickname, sender_id=event.sender.user_id)))
    await pics_bank.finish(msg)


@pics_bank.handle()
async def _(bot: Bot, event: PrivateMessageEvent, state: T_State):
    msg = pb.match(await get_pic_from_url(state['img_list'][0]))
    if msg == '':
        await pics_bank.finish()
    msg = Message(unescape(
        parse(msg=msg, nickname=event.sender.nickname, sender_id=event.sender.user_id)))
    await pics_bank.finish(msg)


pb_add_cmd = on_command('pb添加', rule=check_img, permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN, priority=10)


@pb_add_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    msg = event.get_plaintext().replace(' ', '')
    return_str = re.findall(r"(匹配率(.*?))?(sid(.*?))?发答(.*)", msg, re.S)
    logger.info(return_str)

    if len(return_str) != 0:
        param = {'return_str': return_str[0][4]}
        if '全局' not in msg:
            param['group_id'] = str(event.group_id)
        if return_str[0][1] != '':
            param['limit'] = int(return_str[0][1])
        if return_str[0][4] != '':
            param['sid'] = return_str[0][3]
        await pics_bank.finish(pb.set(await get_pic_from_url(state['img_list'][0]), **param))
    else:
        await pb_add_cmd.finish('参数错误,请检查输入')


pb_del_cmd = on_command('pb删除', permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN)


@pb_del_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    msg = str(event.get_message())
    image_list = get_message_images(event.json())
    param = {}
    if '全局' not in msg:
        param['group_id'] = event.group_id
    else:
        msg.replace('全局', '')
    if len(image_list) == 0:
        await pb_del_cmd.finish(pb.delete(special_id=msg, **param))
    else:
        await pb_del_cmd.finish(
            pb.delete(image_bytes=await get_pic_from_url(image_list[0]), **param))


async def pb_del_first_handle(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip()
    if msg:
        state['is_sure'] = msg


pb_del_all_cmd = on_command('pb删除词库', permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN, handlers=[pb_del_first_handle])
pb_del_all_admin = on_command('pb删除全局词库', permission=SUPERUSER, handlers=[pb_del_first_handle])
pb_del_all_bank = on_command('pb删除全部词库', permission=SUPERUSER, handlers=[pb_del_first_handle])


@pb_del_all_cmd.got('is_sure', prompt='此命令将会清空您的群聊词库，确定请发送 yes/y')
async def _(bot: Bot, event: MessageEvent, state: T_State):
    if state['is_sure'] in ['yes', 'y']:
        if isinstance(event, GroupMessageEvent):
            await pb_del_all_cmd.finish(pb.clean(str(event.group_id)))
        else:
            group_id = str(event.get_message()).strip()
            if group_id.isdigit():
                await pb_del_all_cmd.finish(pb.clean(group_id))  # 私人对话时清空指定群聊的词库
            else:
                await pb_del_all_cmd.finish('参数错误,请使用 pb删除全局词库 来删除全局词库')
    else:
        await pb_del_all_cmd.finish('命令取消')


@pb_del_all_admin.got('is_sure', prompt='此命令将会清空您的全局词库，确定请发送 yes/y')
async def _(bot: Bot, event: MessageEvent, state: T_State):
    if state['is_sure'] in ['yes', 'y']:
        await pb_del_all_admin.finish(pb.clean())
    else:
        await pb_del_all_admin.finish('命令取消')


@pb_del_all_bank.got('is_sure', prompt='此命令将会清空您的全部词库，确定请发送 yes/y')
async def _(bot: Bot, event: MessageEvent, state: T_State):
    if state['is_sure'] in ['yes', 'y']:
        await pb_del_all_bank.finish(pb.clean_all())
    else:
        await pb_del_all_bank.finish('命令取消')
