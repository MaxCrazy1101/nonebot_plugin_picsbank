<!-- markdownlint-disable MD033 MD041-->
<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://raw.githubusercontent.com/nonebot/nonebot2/master/docs/.vuepress/public/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# nonebot_plugin_picsbank

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_✨ 一个根据图片回答的插件 ✨_
<!-- prettier-ignore-end -->

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/nonebot/nonebot2/master/LICENSE">
    <img src="https://img.shields.io/github/license/nonebot/nonebot2" alt="license">
  </a>

## 简介

picsbank是一个根据群友发送的图片做出相应回答的插件，灵感来源于workbank

## 使用

    pb添加[全局][匹配率x][sidxxxx]发(你要应答的图片)答[你要应答的文字]

pb添加 : 指令，添加一个词条

[匹配率x] : 用于指定图片的误差大小，默认为5.默认使用的是插值哈希算法生成64位哈希指纹，计算汉明距离，匹配率x指汉明距离大小。对于.gif只匹配第一帧图像。

[sidxxxx] : xxxx替换为你想使用的标记,可以用来删除词条。不提供时默认为响应句子。

[应答的文字] : 图片匹配成功时返回的句子。

    pb全局添加

参数同上，但只有超级用户使用

    pb删除 [图片][sidxxxx]

pb删除 : 删除指令

[图片] : 要针对的图片,与sid二选一。

[sidxxxx] : 要删除词条的sid,与图片二选一。

    pb全局删除

参数同上，只有超级管理员使用

    pb词库删除 [群号]

删除指定群只有私聊有用(目前有bug)

    pb全局词库删除

    pb全部词库删除

## 即刻开始

- 使用 nb-cli

```
nb plugin install nonebot_plugin_picsbank
```

- 使用 pip

```
pip install nonebot_plugin_picsbank
```

### 常见问题

### 教程/实际项目/经验分享

## 许可证

`noneBot_plugin_picsbank` 采用 `MIT` 协议开源，协议文件参考 [LICENSE](./LICENSE)。

