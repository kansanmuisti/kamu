function emphasize_matching_parts(query, text) {
    var trailing_space = query[query.length - 1] == " ";
    var words = query.ltrim().split(/ +/);
    var cnt = words.length;
    var i;

    if (trailing_space)
        cnt--;
    for (i = 0; i < cnt; i++) {
        var pat = "( |^)(" + words[i] + ")";

        if (i < cnt - 1 || trailing_space)
            pat += "( |$)";
        else
            pat += "(.|$)";
        old_text = text;
        text = text.replace(new RegExp(pat, "ig"),
                            "$1<b>$2</b>$3");
        if (old_text == text)
            return null;
    }

    return text;
}

