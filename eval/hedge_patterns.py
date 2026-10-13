import re

# 否定式边界声明：专门说明某事实"推不出"什么的句式
CORE = re.compile(
    r"不代表|并不代表|不等于|不等同|不能等同|不必然|不一定意味着|不意味着|并不意味|"
    r"不能说明|无法说明|不足以说明|说明不了|并不说明|不能证明|无法证明|不足以证明|证明不了|"
    r"不能认为|不能据此|不能直接(?:得出|推出|说明|认定|下结论|归因)|推不出|不能推出|无法推出|"
    r"不能断定|无法断定|不能简单(?:地)?|不宜简单|不构成|不能当(?:作|成)|不能归因|无法归因"
)
# 对比式框架
CONTRAST = re.compile(r"不是[^。！？\n]{1,40}?而是|而不是|而非|并非")
# 软限定
SOFT = re.compile(r"未必|不一定")

CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def strip_code(text):
    return CODE.sub(" ", text or "")


def count(text):
    t = strip_code(text)
    return {
        "core": len(CORE.findall(t)),
        "contrast": len(CONTRAST.findall(t)),
        "soft": len(SOFT.findall(t)),
        "chars": len(t),
    }


def offending_sentences(text):
    t = strip_code(text)
    out = []
    for s in re.split(r"(?<=[。！？!?；;\n])", t):
        s = s.strip()
        if s and (CORE.search(s) or CONTRAST.search(s)):
            out.append(s)
    return out

# 扩展：同义改写和"待验证"式官腔（只用于测量，不用于 hook）
EXT = re.compile(
    r"仅凭|单凭|光凭|不能替代|无法替代|不能取代|不能只看|不能光看|并不能|不能表明|无法表明|不足以表明|"
    r"不能推断|无法推断|没法(?:说明|证明|判断)|还不能判断|无法判断|不能判断|撑不起|谈不上|说不上|"
    r"有待|仍待|尚待|仍需验证|尚未得到验证|不能直接|不应直接|不要直接|不宜直接"
)


def count_ext(text):
    return len(EXT.findall(strip_code(text)))
