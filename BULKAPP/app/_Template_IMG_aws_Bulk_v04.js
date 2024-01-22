
[
  {
    "type": "link",
    "sizes": [""],
    "tcs": [""],
    "name": "",
    "landing": "",
    "aws_path_1": "",
    "aws_path_2": ".",
    "url": "",

    "add_utm_size": "",
    "viewability": "",
    "impression": ""
  },

  {
    "type": "iframe",
    "sizes": [""],
    "tcs": [""],
    "name": "",
    "landing": "",
    "aws_path_1": "",
    "aws_path_2": ".",
    "link":"",
    
    "add_utm_size": "",
    "viewability": "",
    "impression": ""
  }
]
//** "link": ** 
  //    - "&tc_alt=XXXX" added if "tcs" not empty
  //    - FOR DCOs:
  //      * to pass only utms and tc_alt: DO NOT start with "?" (location.search doesn't work well because it finds two "?")
  //      * to pass only tc: "ONLY_TC"

  // examples: 
  //  "link": "https://www.oxfamintermon.org/es/refugio-seguro?utm_source=&utm_medium=Display&utm_content=PRS,
  //  result -> "&link=https://www.oxfamintermon.org/es/refugio-seguro?utm_source=&utm_medium=Display&utm_content=PRS&tc_alt=84665"

  //  "link": "utm_source=adgravity&utm_medium=dis-rtg-1&utm_campaign=always-on-dco&utm_term=MX",
  //  result -> "&link=utm_source=adgravity&utm_medium=dis-rtg-2&utm_campaign=always-on-dco&utm_term=US&tc_alt=84665"

  //  "link": "ONLY_TC"
  //  result -> "&link=84665"

// ** "add_utm_size": **
  // "add_utm_size": "utm_term=",
  // "add_utm_size": "utm_content=",
  // "add_utm_size": "utm_content=pros_",


,
["EXAMPLES"],
[
  // For Sandos DCO, url comes from feed.
  // In "link" we pass utms (tc_alt is also added), but without the "?", which needs to be added inside the creative
]


[
  {
    "type": "iframe",
    "sizes": ["300x250","300x600","970x250"],
    "tcs": ["111581", "111582","111583"],
    "name": "amresorts-es_v1mp_WAW5-SECRETS_dis-prem_prs-1_COUNTDOWN",
    "landing": "https://www.amrcollection.com/es/",
    "aws_path_1": "AM_RESORTS/2023/09/waw5/secrets/countdown/es/",
    "aws_path_2": "/index.html",
    "link":"https://www.amrcollection.com/es/?utm_source=v1mp&utm_medium=Programmatic&utm_campaign=WAW3-Secrets&utm_term=es",
    "viewability": "//bucket.cdnwebcloud.com/n_one_vway_amr-collection-es_np_",
    "add_utm_size": "utm_content="
  }

  ,

  {
    "type": "iframe",
    "sizes": ["300x250","300x600","970x250"],
    "tcs": ["111585", "111586","111587"],
    "name": "amresorts-es_v1mp_WAW5-DREAMS_dis-prem_prs-1_COUNTDOWN",
    "landing": "https://www.amrcollection.com/es/",
    "aws_path_1": "AM_RESORTS/2023/09/waw5/dreams/countdown/es/",
    "aws_path_2": "/index.html",
    "link":"https://www.amrcollection.com/es/?utm_source=v1mp&utm_medium=Programmatic&utm_campaign=WAW3-Dreams&utm_term=es",
    "viewability": "//bucket.cdnwebcloud.com/n_one_vway_amr-collection-es_np_",
    "add_utm_size": "utm_content="
  }

  ,

  {
    "type": "iframe",
    "sizes": ["300x250","300x600","970x250"],
    "tcs": ["111589", "111590","111591"],
    "name": "amresorts-es_v1mp_WAW5-ALUA_dis-prem_prs-1_COUNTDOWN",
    "landing": "https://www.amrcollection.com/es/",
    "aws_path_1": "AM_RESORTS/2023/09/waw5/alua/countdown/es/",
    "aws_path_2": "/index.html",
    "link":"https://www.amrcollection.com/es/?utm_source=v1mp&utm_medium=Programmatic&utm_campaign=WAW3-Alua&utm_term=es",
    "viewability": "//bucket.cdnwebcloud.com/n_one_vway_amr-collection-es_np_",
    "add_utm_size": "utm_content="
  }


  ,

  {
    "type": "iframe",
    "sizes": ["300x250","300x600","970x250"],
    "tcs": ["111593", "111594","111595"],
    "name": "amresorts-es_v1mp_WAW5-ZOETRY_dis-prem_prs-1_COUNTDOWN",
    "landing": "https://www.amrcollection.com/es/",
    "aws_path_1": "AM_RESORTS/2023/09/waw5/zoetry/countdown/es/",
    "aws_path_2": "/index.html",
    "link":"https://www.amrcollection.com/es/?utm_source=v1mp&utm_medium=Programmatic&utm_campaign=WAW3-Zoetry&utm_term=es",
    "viewability": "//bucket.cdnwebcloud.com/n_one_vway_amr-collection-es_np_",
    "add_utm_size": "utm_content="
  }
]
