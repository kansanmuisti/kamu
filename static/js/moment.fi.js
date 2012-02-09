moment.lang('fi', {
    months : "tammikuu_helmikuu_maaliskuu_huhtikuu_toukokuu_kesäkuu_heinäkuu_elokuu_syyskuu_lokakuu_marraskuu_joulukuu".split("_"),
    monthsShort : "tammi_helmi_maalis_huhti_touko_kesä_heinä_elo_syys_loka_marras_joulu".split("_"),
    weekdays : "maanantai_tiistai_keskiviikko_torstai_perjantai_lauantai_sunnuntai".split("_"),
    weekdaysShort : "ma_ti_ke_to_pe_la_su".split("_"),
    longDateFormat : {
    L : "DD.MM.YYYY",
    LL : "D MMMM YYYY",
    LLL : "D MMMM YYYY HH:mm",
    LLLL : "dddd, D MMMM YYYY HH:mm"
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
    nextWeek: 'dddd [kello] LT',
    lastDay: '[eilen] LT',
    lastWeek: '[viime] dddd[na kello] LT',
    sameElse: 'L'
    },
    relativeTime : {
    future : "%s päästä",
    past : "%s sitten",
    s : "sekunteja",
    m : "minuutti",
    mm : "%d minuuttia",
    h : "tunti",
    hh : "%d tuntia",
    d : "päivä",
    dd : "%d päivää",
    M : "kuukausi",
    MM : "%d kuukautta",
    y : "yksi vuosi",
    yy : "%d vuotta"
    },
    ordinal : function (number) {
    return '.';
    }
});

