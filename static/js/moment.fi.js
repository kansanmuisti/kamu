moment.lang('fi', {
    months : "tammikuu_helmikuu_maaliskuu_huhtikuu_toukokuu_kesäkuu_heinäkuu_elokuu_syyskuu_lokakuu_marraskuu_joulukuu".split("_"),
    monthsShort : "tammi_helmi_maalis_huhti_touko_kesä_heinä_elo_syys_loka_marras_joulu".split("_"),
    weekdays : "maanantai_tiistai_keskiviikko_torstai_perjantai_lauantai_sunnuntai".split("_"),
    weekdaysShort : "ma_ti_ke_to_pe_la_su".split("_"),
    longDateFormat : {
    LT : "HH:mm",
    L : "DD.MM.YYYY",
    LL : "D. MMMM[ta] YYYY",
    LLL : "D. MMMM[ta] YYYY HH:mm",
    LLLL : "dddd, D. MMMM[ta] YYYY HH:mm"
    },
    meridiem : {
    AM : 'AM',
    am : 'am',
    PM : 'PM',
    pm : 'pm'
    },
    calendar : {
    sameDay: "[tänään] LT",
    nextDay: '[huomenna] LT',
    nextWeek: 'dddd[na] LT',
    lastDay: '[eilen] LT',
    lastWeek: '[viime] dddd[na] LT',
    sameElse: 'L'
    },
    relativeTime : {
    future : "%s päästä",
    past : "%s sitten",
    s : "sekunteja",
    m : "1 minuutti",
    mm : "%d minuuttia",
    h : "1 tunti",
    hh : "%d tuntia",
    d : "1 päivä",
    dd : "%d päivää",
    M : "1 kuukausi",
    MM : "%d kuukautta",
    y : "1 vuosi",
    yy : "%d vuotta"
    },
    ordinal : function (number) {
    return '.';
    }
});
