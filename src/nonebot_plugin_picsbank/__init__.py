import re
import copy
from typing import Union

from nonebot.params import Depends
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.message import handle_event
from nonebot import require, on_command, on_message
from nonebot.permission import SUPERUSER, SuperUser
from nonebot.internal.matcher.matcher import Matcher
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_waiter")
require("nonebot_plugin_alconna")
require("nonebot_plugin_userinfo")

from nonebot_plugin_waiter import prompt
from nonebot_plugin_userinfo import UserInfo, EventUserInfo
from arclet.alconna import Args, Option, Alconna, CommandMeta, store_true
from nonebot_plugin_alconna import Image, Match, Query, MsgTarget, UniMessage, on_alconna

from .utils import get_pic_from_url
from .data_source import pic_bank as pb

__version__ = "0.1.4"

__plugin_meta__ = PluginMetadata(
    name="图片词库",
    description="据群友发送的图片做出相应回答",
    usage="""
pb添加 [匹配率+(64以下数字)][sid(任意特殊标记，可用于删除词条)][图片][回答]....
    例: pb添加匹配率5sidnihao[这是一张图片]我爱你
pb全局添加, 构成如上, 但只有超级用户使用
pb删除 [sid/图片], 群主 群管理员 超级用户可用
pb全局删除 [sid/图片], 只有超级用户使用
pb全部词库删除
""",
    homepage="https://github.com/MaxCrazy1101/nonebot_plugin_picsbank",
    type="application",
    config=None,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna", "nonebot_plugin_userinfo"),
    extra={
        "author": "Alex Newton",
        "priority": 1,
        "version": __version__,
    },
)


async def check_img(bot: Bot, event: Event, state: T_State) -> bool:
    msg = UniMessage.generate_without_reply(event=event, bot=bot)
    if msg.has(Image):
        imgs = msg[Image]
        urls = [img.url for img in imgs if img.url]
        if urls:
            state["img_list"] = urls
            return True
    return False


pics_bank: type[Matcher] = on_message(rule=check_img, priority=98)  # 优先级比word_bank略高


@pics_bank.handle()
async def _(bot: Bot, event: Event, state: T_State, user: UserInfo = EventUserInfo()):
    try:
        target = UniMessage.get_target()
        group_id = target.id if not target.private else None
    except Exception:
        group_id = None
    if group_id is not None:
        msg = pb.match(await get_pic_from_url(state["img_list"][0]), group_id)
    else:
        msg = pb.match(await get_pic_from_url(state["img_list"][0]))
    if msg == "":
        await pics_bank.finish()
    iscommand, to_bot = False, False
    if "/command" in msg:
        iscommand = True
        msg = msg.replace("/command", "")
    if "/atbot" in msg:
        to_bot = True
        msg = msg.replace("/atbot", "")
    send_msg = (
        await UniMessage.template(msg)
        .format(
            nickname=user.user_displayname or user.user_name,
            sender_id=user.user_id,
            bot_id=bot.self_id,
        )
        .export(bot=bot, fallback=True)
    )
    if iscommand:
        event_new = copy.deepcopy(event)

        def _patch_get_message(_):
            return send_msg

        event_new.get_message = _patch_get_message.__get__(event_new)
        if to_bot:
            event_new.is_tome = (lambda _: True).__get__(event_new)
        await handle_event(bot, event_new)
        await pics_bank.finish()
    else:
        await pics_bank.finish(msg)


pb_add_cmd = Alconna(
    "pb添加",
    Args["img", Image]["answer", str],
    Option("匹配率", Args["limit", int, 5], help_text="匹配率", compact=True),
    Option("sid", Args["tag", str, "_"], help_text="指定词条标记", compact=True),
    Option("--global", action=store_true, default=False, help_text="全局模式"),
    meta=CommandMeta(
        "添加一个词条",
        usage="""\
[匹配率x]: 用于指定图片的误差大小，默认为5.
    默认使用的是插值哈希算法生成64位哈希指纹，计算汉明距离，匹配率x指汉明距离大小。
    对于.gif只匹配第一帧图像。
[sidxxxx]: 特殊标记，可用于删除词条。
        """,
        example="""\
pb添加匹配率5sidnihao[这是一张图片]我爱你
pb全局添加... # 只有超级用户使用
""",
    ),
)

pb_add = on_alconna(
    pb_add_cmd,
    use_cmd_start=True,
    auto_send_output=True,
    # FIXME:
    # permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN,
    priority=10,
    block=True,
)


def wrapper(slot, content):
    if slot == "limit":
        if content is None:
            return 5
        return int(content)
    if content is None:
        return "_"
    return content


pb_add.shortcut(
    r"pb添加(匹配率(?P<limit>\d+))?(sid(?P<sid>.+))?",
    arguments=["匹配率", "{limit}", "sid", "{sid}"],
    prefix=True,
    wrapper=wrapper,
    humanized="pb添加[匹配率][sid]",
)

pb_add.shortcut(
    r"pb全局添加(匹配率(?P<limit>\d+))?(sid(?P<sid>.+))?",
    arguments=["匹配率", "{limit}", "sid", "{sid}", "--global"],
    prefix=True,
    wrapper=wrapper,
    humanized="pb全局添加[匹配率][sid]",
)


@pb_add.handle()
async def _(
    target: MsgTarget,
    img: Image,
    answer: str,
    limit: Match[int],
    tag: Match[str],
    is_global: Query[bool] = Query("global.value"),
    is_superuser=Depends(SuperUser),
):
    if target.private:
        await pb_add.finish("该命令在私聊场景不可用")
    if not img.url:
        await pb_add.finish("图片链接获取失败")
    content = re.sub(r"/at(\d+)", lambda mat: f"{{:At(user, {mat[1]})}}", answer)
    content = content.replace("/atself", "{:At(user, sender_id)}")
    content = content.replace("/self", "{nickname}")
    param = {"return_str": content, "limit": limit.result if limit.available else 5}
    if is_global.result and not is_superuser:
        pb_add.skip()
    if not is_global.result:
        param["group_id"] = target.id
    if tag.available and tag.result != "_":
        param["sid"] = tag.result
    await pb_add.finish(pb.set(await get_pic_from_url(img.url), **param))


pb_del_cmd = Alconna(
    "pb删除",
    Args["content#图片或者sid", [str, Image]],
    Option("--global", action=store_true, default=False, help_text="全局模式"),
    meta=CommandMeta(
        "删除一个词条",
        usage="[content]: 指定的图片或用于删除词条的特殊标记。",
        example="""\
pb删除 [sid/图片]
pb全局删除 [sid/图片]  # 只有超级用户使用
""",
    ),
)

pb_del = on_alconna(
    pb_del_cmd,
    use_cmd_start=True,
    auto_send_output=True,
    # FIXME:
    # permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN,
    priority=10,
    block=True,
)

pb_del.shortcut("pb全局删除", arguments=["--global"], prefix=True)


@pb_del.handle()
async def _(
    target: MsgTarget,
    content: Union[str, Image],
    is_global: Query[bool] = Query("global.value"),
    is_superuser=Depends(SuperUser),
):
    if target.private:
        await pb_del.finish("该命令在私聊场景不可用")
    if is_global.result and not is_superuser:
        pb_add.skip()
    if isinstance(content, str):
        await pb_del.finish(pb.delete(special_id=content, group_id="0" if is_global.result else target.id))
    else:
        if not content.url:
            await pb_del.finish("图片链接获取失败")
        await pb_del.finish(
            pb.delete(image_bytes=await get_pic_from_url(content.url), group_id="0" if is_global.result else target.id)
        )


pb_del_all_cmd = Alconna(
    "pb词库删除",
    Args["group_id?#群号", str],
    Option("--global", action=store_true, default=False, help_text="全局模式"),
    meta=CommandMeta(
        "删除词库",
        usage="私聊下非全局模式需要传入群号",
        example="""\
pb词库删除 [群号]
pb全局词库删除
""",
    ),
)

pb_del_all = on_alconna(
    pb_del_all_cmd,
    use_cmd_start=True,
    auto_send_output=True,
    # FIXME:
    # permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN,
    priority=10,
    block=True,
)

pb_del_all.shortcut("pb全局词库删除", arguments=["--global"], prefix=True)


pb_del_all_bank = on_command(
    "pb全部词库删除",
    permission=SUPERUSER,  # handlers=[pb_del_first_handle]
)


@pb_del_all.handle()
async def _(
    target: MsgTarget,
    group_id: Match[str],
    is_global: Query[bool] = Query("global.value"),
    is_superuser=Depends(SuperUser),
):
    if is_global.result and not is_superuser:
        pb_add.skip()
    ans = await prompt("此命令将会清空您的群聊词库，确定请发送 yes/y", timeout=30)
    if not ans:
        await pb_del_all.finish("命令取消")
    text = ans.extract_plain_text()
    if not text:
        await pb_del_all.finish("命令取消")
    if text.lower in {"yes", "y"}:
        if is_global.result:
            pb.clean()
            await pb_del_all.finish("全局词库清理成功")
        if target.private:
            if not group_id.available:
                await pb_del_all.finish("非全局模式请传入群号")
            await pb_del_all.finish(pb.clean(group_id.result))  # 私人对话时清空指定群聊的词库
        else:
            await pb_del_all.finish(pb.clean(target.id))
    await pb_del_all.finish("命令取消")


@pb_del_all_bank.handle()
async def _():
    ans = await prompt("此命令将会清空全部词库，确定请发送 yes/y", timeout=30)
    if not ans:
        await pb_del_all.finish("命令取消")
    text = ans.extract_plain_text()
    if not text:
        await pb_del_all.finish("命令取消")
    if text.lower in {"yes", "y"}:
        await pb_del_all_bank.finish(pb.clean_all())
    await pb_del_all.finish("命令取消")
