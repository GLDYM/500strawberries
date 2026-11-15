# 100% Orange Juice 存档字段说明（3.29.2.0）

本文说明 `.ojs` 解密后的 JSON 结构，以及每个数值/下标的**合法范围**。
范围来源有三类，文中会标注：

- **类型**：IDA 里该字段落到的 C 类型（`_BYTE` / `_WORD` / `_DWORD` / bool / string），决定了存储上限。
- **长度**：该字段是"每个游戏实体一项"的数组，数组长度就是实体总数，下标范围即 `0 .. 长度-1`。
- **语义**：例如 `progress` 用 `-1` 表示未开始、`0..100` 表示进度。

容器格式（CRC / HMAC / ChaCha / LZ4）见 [README](README.md#L33)。

## 0. 读取方式

JSON 数字在解析时接受 int 或 double（`sub_1410F82F0` 里按 JSON 节点类型 4/5/6/7 分支），
最后按目标 C 类型截断存入结构体：

| JSON 节点类型 | 处理 | 结果 |
|---|---|---|
| 4 | `(unsigned __int8)node[8]` | 1 字节 |
| 5 / 6 | `*((_DWORD *)node + 2)` | 32 位整数 |
| 7 | `(int)*((double *)node + 1)` | double 截断成 int |

所以：

- 存储为 `_BYTE` 的字段：合法值 `0..255`
- 存储为 `_WORD` 的字段：合法值 `0..65535`
- 存储为 `_DWORD` 的字段：合法值 `0..4294967295`（有符号解释时 `-2147483648..2147483647`）
- bool：`true` / `false`
- 超出类型范围的值会被截断（不是报错）；**没有额外校验的字段，游戏会照单全收**，越界语义由后续逻辑决定。

## 1. 顶层结构

| key | 含义 | 结构 |
|---|---|---|
| campaigns | 剧情模式通关记录 | `camp_list[83]` |
| cards | 卡牌拥有表 + 卡组 | `list[955]`, `deck_list[101]` |
| codex | 图鉴/故事 | `entries[99]`, `stories[8]` |
| coop | 合作模式卡组与 BOSS 记录 | `decks[6]`, `defeated_bosses[7]` |
| cosmetics | 装扮（配色/头饰） | `current[2]`, `saved[101]`, `headwear_hairs[101]` |
| events | 历年活动进度（2017–2026） | 按年份/活动嵌套 |
| filters | 联机房间筛选器 | 4 个列表 |
| goods | 商店/库存道具 | `goods[3472]` |
| info | 玩家主信息 | 35 个字段 |
| misc | 各种解锁标志/活动点数 | 25 个字段 |
| pets | 宠物 | `current`, `last_used[3]` |
| taunts | 嘲讽语音 | `ids[59]`, `arrays[59]` |
| unlocks | 解锁表（背景/边框/骰子/表情等） | 12 个列表 |

每个 section 由一个函数负责读写（IDA，3.29.2.0）：

| 函数 | section |
|---|---|
| sub_1410F82F0 | info |
| sub_1410FAE90 | cards |
| sub_141103960 | goods |
| sub_1411057A0 | cosmetics |
| sub_14110C260 | campaigns |
| sub_14110C6B0 | pets |
| sub_14110CA50 | coop |
| sub_141100CD0 | taunts |
| sub_141102550 | codex |
| sub_141102DE0 | filters |
| sub_1410FC340 | unlocks |
| sub_1410FF5C0 | misc |
| sub_14110E420 | events |

## 2. info —— 玩家主信息

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| version_int | int32 | 存档版本号 | 0..2^32-1；本档 2437 |
| user_name | string | 玩家名 | 任意 UTF-8 |
| index | int32 | 槽位/序号（通常 0） | 0..2147483647 |
| lastUsedSaveSlot | uint8 | 上次使用槽位 | 0..255（实际 0..2） |
| personal_pc_code | int32 | 自定义 PC 码 | 0..2^32-1 |
| start_unit | int32 | 默认出战角色 | 0..100（角色共 101 个） |
| profileUnit | int32 | 资料卡角色 | 0..100 |
| profileUnitColor | int32 | 角色配色 | 0..该角色配色数-1 |
| profileHairColor | int32 | 发色 | 同上 |
| profileHeadwear | int32 | 头饰 | 0..40（headwear 列表 41 项） |
| profileDice | uint16 | 骰子皮肤 | 0..65535（dice 表 70 项） |
| profileHomemark | uint16 | 基地标记 | 0..65535（homemark 表 41 项） |
| currentPin | int32 | 徽章 | 0..64（pins 65 项） |
| currentBackground | int32 | 背景 | 0..140（backgrounds 141 项） |
| currentBorder | int32 | 边框 | 0..43（borders 44 项） |
| currentDifficulty | int32 | 默认难度 | 0..4 |
| orangeCurrency | int32 | 橙子 | 0..2147483647 |
| star_num | int32 | 星星 | 0..2147483647 |
| play_num | int32 | 游戏局数 | 0..2147483647 |
| play_time | object | 游戏时长 | 5 个 int32：year, yday, hour, min, sec |
| pocket_card_num | int | 拥有卡牌种类数 | 0..954（cards.list 长度 955） |
| scenario_num | int32 | 已解锁剧本数 | 0..82（camp_list 长度 83） |
| goods_num | int | 道具记录数 | 0..3471（goods 长度 3472） |
| card_kind | int | 卡组类型 | 0..N |
| cardbacks_current | int | 当前卡背 | 0..8（cardbacks_unlocked 9 项） |
| cardbacks_unlocked | list[int] | 已解锁卡背 | 元素 0..8 |
| FBFcustomLevelsAvailable | list[300] bool | 自定义关卡可用 | 每项 0/1 |
| lulu_eggeffectreceived | list[3] int | 幸运蛋记录 | 元素 0..2 |
| dlulu_eggeffectreceived | list[3] int | 同上（每日） | 元素 0..2 |
| cutscenes | list 或 null | 已看过场 | 元素 {index, value} |
| read10YearAnniversaryMessage 等 | bool | 各种一次性标志 | 0/1 |

### 2.1 daily_challenges（每日挑战，固定 3 条）

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| type | int32 | 挑战类型 | 0..挑战种类数-1 |
| targetValue | int | 目标值 | 0..2147483647 |
| currentValue | int | 当前值 | 0..targetValue |
| unitA | int | 角色 A | 0..100 |
| unitB | int | 角色 B | 0..100；0 表示不限定 |
| fieldA | int | 场地 A | 0..场地数-1 |
| fieldB | int | 场地 B | 同上 |
| cardA | int | 卡牌 A | 0..954；0 表示不限定 |
| cardB | int | 卡牌 B | 同上 |
| expirationDate | int | 过期时间（unix） | 0..2^32-1 |
| redeemed | bool | 是否已领取 | 0/1 |

## 3. cards —— 卡牌

**cards.list[955]**：拥有表，每个元素只有 `{ "id": int }`。

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| id | int32 | 卡牌 id | 0..954（1:1 对应 955 个卡牌位） |

**cards.deck_list[101]**：每个角色一个卡组容器。

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| index | int | 角色索引 | 0..100 |
| decks | list of list[int] | 每个角色若干套卡组（通常 5 套），每套是卡牌 id 列表 | 元素 0..954；每套长度 ≤ 卡组上限（约 50） |

## 4. codex —— 图鉴与剧情

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| entries | list[99] of {index, value} | 图鉴条目 | index 0..98；value 0..299 |
| stories | list[8] of {index, progress[3], seen} | 故事进度 | index 0..N；progress 元素 0..10；seen 0/1 |
| seen_intro | bool | 是否看过开场 | 0/1 |
| has_imported | bool | 是否导入过旧档 | 0/1 |

## 5. campaigns —— 剧情通关

**camp_list[83]**：每个剧本一项。

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| id | int32 | 剧本 id | 0..82 或 300+（DLC 编号区间） |
| clear | uint8 | 通关状态 | 0..255（实际按难度位记录，常见 0..7） |

## 6. coop —— 合作模式

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| decks | list[6] of {class_id, data[101]} | 每个职业的卡组 | class_id 0..5；data 按角色 101 项 |
| defeated_bosses | list[7] of {id, difficulty} | BOSS 击杀记录 | id 0..BOSS 数-1；difficulty 0..3 |

## 7. cosmetics —— 装扮

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| current | list[2] of {...} | 当前装扮（玩家/单人） | 元素见下 |
| saved | list[101] of list | 每个角色的已保存装扮 | 外层 0..100 |
| headwear_hairs | list[101] of {id, headwear[41]: bool} | 每个角色的头饰解锁 | id 0..100；headwear 每项 0/1 |

current / saved 元素字段：

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| unit_costume | int | 服装 | 0..该角色服装数-1 |
| unit_color | int | 配色 | 0..该角色配色数-1 |
| unit_pose | int | 姿势 | 0..该角色姿势数-1 |
| hair_color | int | 发色 | 0..发色数-1；-1 表示默认 |
| headwear | int | 头饰 | 0..40；-1 表示无 |
| extra_headwear | int | 额外头饰 | 同上 |
| extra_unitcolor | int | 额外配色 | 0..N |

## 8. filters —— 房间筛选

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| characters | list[78] int | 选中的角色 | 元素 0..100 |
| events | list[8] int | 选中的活动 | 元素 0..活动数-1 |
| levels | list[9] int | 选中的等级区间 | 元素 5..35 |
| coop_levels | null 或 list | 合作难度筛选 | 元素 0..N |

## 9. goods —— 道具库存

**goods[3472]**：每个道具一项。

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| id | string | 道具内部名，如 accessory_pigformation_fernet | 固定字符串 |
| count | int32 | 持有数量 | 0..2147483647 |
| stock | int32 | 商店库存 | 0..2147483647 |

## 10. pets —— 宠物

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| current | int32 | 当前宠物 | 0..宠物数-1（本档 97） |
| last_used | list[3] int | 最近使用的宠物 | 元素 -1..N；-1 表示空 |

## 11. taunts —— 嘲讽语音

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| ids | list[59] int | 角色/语音 id | 元素 1..87 |
| arrays | list[59] of list | 每个角色绑定的语音 | 内层为 int 列表 |

## 12. unlocks —— 解锁表

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| backgrounds | list[141] int | 已解锁背景 | 元素 0..153 |
| borders | list[44] int | 已解锁边框 | 元素 0..44 |
| pins | list[65] int | 已解锁徽章 | 元素 0..69 |
| emojis | list[780] int | 已解锁表情 | 元素 200..3014（表情 id 区间） |
| dice | list[70] of {sortID, type, unlocked} | 骰子 | unlocked 0/1 |
| homemark | list[41] of {sortID, type, unlocked} | 基地标记 | unlocked 0/1 |
| general | list[22] of {type, status, progress} | 通用解锁项 | status 0/1；progress ≥0 |
| hairs | list[101] of list | 每个角色已解锁发型 | 外层 0..100 |
| poses | list[101] of list | 每个角色已解锁姿势 | 外层 0..100 |
| unit_colors | list[101] of list | 每个角色已解锁配色 | 外层 0..100 |
| extra_colors | list[101] of list | 每个角色额外配色 | 外层 0..100 |
| unit_seen | list[23] int | 已见过的角色 | 元素 20052..20075 |

## 13. events —— 历年活动

结构是 `events.<年份>.<活动名>.<字段>`，年份 2017–2026，活动名如 `christmas`
`valentine` `halloween` `spring` `summer` `winter` `fall` `mio` `poppo` `chaos`。
每个活动只出现自己的字段子集，但数值规则统一：

| 字段模式 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| progress | int32 | 活动进度 | -1（未开始）.. 100 |
| clear_status | int32 或 bool | 是否通关 | 0/1 |
| previously_completed | int32 或 bool | 历史是否通关过 | 0/1 |
| games_played / games_won | int32 | 局数 | 0..2147483647 |
| games_since_last_random_item_drop | int32 | 距上次随机掉落 | 0..2147483647 |
| games_since_last_* | int32 | 各类保底计数 | 0..2147483647 |
| currency / total_candy / decorations / score / stamp_count 等 | int32 | 活动货币/积分 | 0..2147483647 |
| current_panel | int32 | 当前走到的格子 | -1（未开始）或 0..格子数-1 |
| last_played | int32 | 上次游玩 unix 时间 | 0..2^32-1 |
| last_played_arr | list[12] int | 日期分解 | 各元素 0..9999 |
| retirement_goals | object | 退休目标计数 | 每个字段 0..2147483647 |
| retirement_progress | list[int] | 退休进度 | 元素 0..2147483647 |
| retirement_unlocked / unlocked_* / saw_* / flags.* | bool | 标志位 | 0/1 |
| milestones / flags / goals / bounties_defeated | object | 一组 bool 或计数 | bool 或 ≥0 |
| active_event_type | int32 | 当前活动类型 | 0..活动类型数-1 |

## 14. misc —— 杂项解锁

| 字段 | 类型 | 含义 | 合法范围 |
|---|---|---|---|
| FBFidolPoppoProgress | int32 | 偶像活动进度 | 0..N |
| FBFidolPoppoAvailable | bool | 是否开放 | 0/1 |
| FBFstarDevPoppoProgress | int32 | 星之开发进度 | 0..N |
| FBFstarDevPoppoAvailable | bool | 是否开放 | 0/1 |
| FBFwhiteSuitPoppoProgress | int32 | 白西装进度 | 0..N |
| FBFbigPoppoCostumeAvailable | bool | 大 Poppo 服装 | 0/1 |
| FBFExtremeDiceAvailable | bool | 极限骰子 | 0/1 |
| FBFhalloweenUnlockPoints | uint8 | 万圣节点数 | 0..255 |
| FBFXmasHatUnlockPoints | int32 | 圣诞帽点数 | 0..2147483647 |
| FBFhalloweenCostumesAvailable | string | 解锁标记 | "UNLOCK" 或空 |
| FBFxmasHatAvailable | string | 解锁标记 | "UNLOCK" 或空 |
| halloweenCandyPoints | int32 | 万圣节点数 | 0..2147483647 |
| christmasCandyPoints | int32 | 圣诞点数 | 0..2147483647 |
| poppoEvent2Points | uint16 | Poppo 活动点数 | 0..65535 |
| radPoppo2Available | uint16 | 标志 | 0..65535（实际 0/1） |
| hair9KrilaUnlockProgress | int32 | 发型解锁进度 | 0..N |
| ckPoints | uint8 | 点数 | 0..255 |
| tutorial_was_read | int32 | 教程已读 | 0/1 |
| seenIntroPlayerPlate | bool | 看过开场名牌 | 0/1 |
| bountyHunt_HarbingerDefeated | bool | 击杀记录 | 0/1 |
| unlockSweetBreakerVoiceline | bool | 语音解锁 | 0/1 |
| unlockedIslayChibi | bool | 解锁记录 | 0/1 |
| unlockedPoppoSong | bool | 歌曲解锁 | 0/1 |
| received_starter_booster | bool | 新手包已领 | 0/1 |
| shop_purchases / transactions | list | 商店流水（3.29 新增） | 元素 {timestamp, amount} |

## 15. 修改时的注意事项

1. **数组长度不要改**。列表长度对应游戏内实体数量（955 张卡、3472 个道具、101 个角色…），
   增删元素会让下标错位。
2. **数值不要越过 C 类型上限**。例如 `lastUsedSaveSlot` 是 uint8，写 300 会被截成 44；
   `orangeCurrency` 是 int32，写到 2^31 会变成负数。
3. `-1` 在 `progress` / `current_panel` / `last_used` 里表示"未设置"，不要随手改成 0。
4. 改完必须重新计算容器层的 CRC 和 HMAC —— `encryptSave` 已自动处理，见
   [main.py](main.py) 和 [README](README.md#L33)。
5. 容器里的 key material 必须保持与原档一致（游戏会校验 ChaCha 常量），
   `main.py` 会自动从同目录的 `.ojs` 读回。

## 16. 范围是怎么得出的

- **类型**：在 IDA 里反编译每个 section 的读取函数（见第 1 节的表），
  每个字段 key 后紧跟一条 `*((_BYTE|_WORD|_DWORD|_QWORD *)qword_14265F728 + N) = ...`，
  目标类型就是这个字段的存储宽度。例如：

      strcpy(..., "star_num")
      v36 = ...                                  // 取 JSON 数字
      *((_DWORD *)qword_14265F728 + 36) = v36    // int32

- **长度**：数组字段的长度直接等于该实体在游戏里的总数，所以下标范围是
  `0 .. len-1`；本档的 955 / 3472 / 101 / 83 / 99 等就是当前版本的实体数。
- **语义**：`progress` 的 `-1`、`last_used` 的 `-1` 等来自实际存档观察与代码里的哨兵值判断。
## 17. 全解锁存档

    python make_full_unlock.py profile0.ojs profile0_full

生成 `profile0_full.ojs`（可直接替换存档）和 `profile0_full.json`。
脚本复用源档的 key material 重新封装，游戏那边的 ChaCha 常量校验仍然通过。

解锁内容：

| 项目 | 做法 |
|---|---|
| campaigns | 全部 `clear = 7` |
| cosmetics.headwear_hairs | 每个角色 41 个布尔位全 true |
| unlocks.hairs / poses / unit_colors / extra_colors | 101×N 布尔矩阵全 true |
| unlocks.dice / homemark / general | 70 / 41 / 22 项的 `unlocked`/`status` 全 true |
| unlocks.backgrounds | 0..187（对应 playerplate/bg_N.png，共 188 个） |
| unlocks.borders | 0..44（playerplate/border_N.png，45 个） |
| unlocks.pins | 1..80（playerplate/pins/pin_N_0.png，80 个，**从 1 开始**） |
| info.FBFcustomLevelsAvailable | 300 项全 true |
| codex.entries | 补全到 0..101（原档缺 53 / 88 / 101） |
| codex.stories | `seen = true`，`progress` 里的 0 改成 1 |
| misc | 所有布尔解锁位 true |
| info | 橙子/星星设为 9999999 |

**不要动的字段**：

- `goods[].count`：**0 表示已购买**（游戏里越买越小），改成 1 反而会变成"可再次购买"。
  原档 3472 项全是 0，已经是全买状态。
- `unlocks.emojis`：表情 id（200..3014）不对应任何资源文件名，无法安全枚举全部 id。
- `events`：逐年活动 `progress` 语义不统一（有的是 -1..100，有的是 0/1），强改会错乱。

**已经就是全满的**：

- `info.cardbacks_unlocked` = 0..8：`cardsystem/backs/back_0..back_8` 就是全部 9 个卡背。

**还差的部分**：

- 每个单位一条的数组（`cosmetics.saved`、`cosmetics.headwear_hairs`、`cards.deck_list`、
  `unlocks.hairs/poses/unit_colors/extra_colors`、`coop.decks[].data`）长度都是 **101**（单位 0..100）。
  如果游戏里存在第 102 个单位（id 101），需要在这些数组末尾各追加一条，否则该角色没有
  装扮/卡组/解锁数据。
