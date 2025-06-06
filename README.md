https://console.apify.com/actors/nfp1fpt5gUlBwPcor/runs/tZwiz4P0vYT1NkBlP#output

# Demo Day Guest Researcher
Generates in depth digital footprint on a person of choice.

Inputs: name of person
Outputs: document containing all recent viral posts LinkedIn and X Posts, all recent podcasts and transcripts

## workflow
```mermaid
---
config:
  theme: base
---
flowchart TD
 s[Input: Name]
 subgraph tw["Scrape Twitter Posts"]
        twB["Document -- All Twitter Posts"]
        twA["AI Agent"]
  end
 subgraph li["Scrape Linkedin Posts"]
        liB["Document -- All LinkedIn Posts"]
        liA["AI Agent"]
  end
 subgraph pod["Scrape Podcasts"]
        podB["Apple Podcast Scraper"]
        podA["AI Agent"]
        podC["Spotify Podcast Scraper"]
        podD["APIFY: Youtube Podcast Scraper"]
        podE["Document -- All Podcast Questions"]
  end
 subgraph ap["Automated Prep"]
        tw
        li
        pod
        result["VC Cheat Sheet"]
  end
 subgraph fa["Further Actions"]
        faA["Manual Review of Document"]
        faC["Sean Attends Demo Day and Uses Research"]
        faB{"Sufficient Research?"}
        faE["Further Tailored Cheat Sheet"]
        faD["AI Agent"]
        faG["Sean Provides Feedback to Tom"]
  end
    s --> twA
    s --> liA
    s --> podA
    twA --> twB
    liA --> liB
    podA -- scrape podcast links --> podB & podC & podD
    podB -- transcript --> podE
    podC -- transcript --> podE
    podD -- transcript --> podE
    podE -- add to --> result
    twB -- add to --> result
    liB -- add to --> result
    result --> faA
    faA --> faB
    faB -- yes --> faC
    faB -- no; input detailed prompt and VC Cheat Sheet --> faD
    faD --> faE
    faE --> faB
    faC --> faG
    faG --> faH["Output: VC Cheat Sheet"]
    twB@{ shape: lin-doc}
    twA@{ shape: trap-b}
    liB@{ shape: lin-doc}
    liA@{ shape: trap-b}
    podB@{ shape: trap-b}
    podA@{ shape: trap-b}
    podC@{ shape: trap-b}
    podD@{ shape: trap-b}
    podE@{ shape: lin-doc}
    result@{ shape: docs}
    faE@{ shape: docs}
    faD@{ shape: trap-b}
```

# 