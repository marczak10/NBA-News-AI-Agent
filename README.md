# 🏀 NBA News AI Agent Project

Welcome to the **NBA News AI Agent Project** repository.
This project is an AI workflow that collects NBA news from different sources, summarizes it, removes duplicate stories, ranks the most relevant articles based on user preferences, and sends one daily email digest with the top stories.

The idea is simple: instead of reading everything from different media outlets, the agent finds the most important stories for you and puts them in one place.

---

## 🌟 Project Goal

The goal of this project is to build a useful AI NBA news assistant.
It is designed to save time, reduce noise, and deliver the stories that actually matter in a short daily briefing.

---

## ⚙️ How It Works

Every time the workflow runs, it does this:

1. Scrapes fresh NBA content from **NBA.com**, **ESPN**, and selected **YouTube channels**
2. Stores that content in **PostgreSQL**
3. Uses an OpenAI-powered agent to create a short summary for each item
4. Removes repeated or very similar stories
5. Ranks the remaining stories based on a user profile
6. Sends the final news update by email

The workflow is built with **LangGraph**, so each step is handled in order:

```text
Scrape -> Ingest -> Summarize -> Deduplicate -> Rank -> Email
```

---

## 🧠 How Duplicate Stories Are Removed

This is one of the most important parts of the project.
Breaking news often shows up multiple times across different sites, and the goal is to avoid sending the same story in slightly different wording.

After summaries are created, the project generates an embedding for each summary using OpenAI embeddings.
That turns every summary into a numeric vector.

Then the workflow:

- Compares summaries using **cosine similarity**
- Groups summaries that are very close to each other in meaning
- Treats those groups as clusters of the same story
- Keeps the most recent summary from each cluster

In simple terms:

- If two summaries are talking about the same injury update, trade rumor, or game result, their vectors should be close
- A high cosine similarity means the summaries are semantically similar
- If similarity passes the threshold, they are grouped together
- Only one version of that story moves forward to the ranking step

This helps the final email feel cleaner and more useful, because it focuses on unique stories instead of repeating the same news from different sources.

---

## 🎯 Personalization

The agent does not rank stories randomly.
It uses a user profile to decide what matters most.

That profile can include:

- Favorite teams
- Favorite players
- Interest in injuries, trades, standings, and playoff impact
- Preference for important news over hype or filler

Because of that, the final digest feels more like a personalized briefing than a generic news feed.

---

## 📧 Example Daily Email

The real email is sent in plain text and HTML.
Below is a simple **markdown-style example** of what the digest looks like:

```md
# AI NBA News Daily Summary

Hi Jakub - happy March 30, 2026!

Today's top stories kick off with major NBA separation: Detroit clamps down in a dominant win,
Atlanta surges in the East, and playoff seeding permutations begin to take shape now that the
field is set. We'll also cover key injury and availability swings - Curry's knee setback and
Moody's successful surgery - as well as big-picture postseason implications from Milwaukee's
elimination to Cleveland's record-breaking rout, plus standout college hoops as Illinois books
a Final Four berth.

## Top 10 NBA News Articles for March 29, 2026

### 1. Pistons Dismantle Wolves as Hawks Roll Past Kings
Detroit dominated Minnesota behind elite defense, limiting the Timberwolves to 32% shooting and
21% from 3 in a 109-87 win on ABC/ESPN. Atlanta kept its hot stretch alive with a 123-113 win
over Sacramento, moving within 0.5 games of fifth in the East as Jalen Johnson and Nickeil
Alexander-Walker led a balanced scoring attack. The day's other highlights included strong two-way
stat lines from Joel Embiid and Paul George in a 118-114 Sixers win over Charlotte and Victor
Wembanyama's 23-15-6 line in San Antonio's 127-95 rout of Milwaukee.

[Read more](https://example.com/article-1)

### 2. Seeding races kick off after playoff field set
With the Bucks officially eliminated, all 20 playoff teams are now locked in, but multiple
seeding and play-in matchups are still being decided. In the East, the Celtics' road game at
Charlotte and the Magic-Raptors matchup could reshuffle the 8/9 and 5/6/7 picture, while the
West's biggest swing features OKC vs. the Knicks as San Antonio's tiebreaker advantage keeps the
Spurs' path to No. 2 alive. The article also lays out clinching scenarios, projected standings
via ESPN BPI, and how lottery odds and pick protections could shift for teams like Indiana,
Washington, and Utah depending on playoff outcomes.

[Read more](https://example.com/article-2)

### 3. Sunday Night Basketball Live Updates: Knicks-OKC, Warriors-Nuggets
NBA.com's live blog tracks a 9-game Sunday, spotlighting primetime matchups including Knicks at
Thunder and Warriors at Nuggets, alongside Clippers-Bucks and Heat-Pacers. Oklahoma City tries
to extend its winning streak over New York while Golden State and Denver both have streaks and
playoff-position implications on the line. The blog also logs early-game injury news, including
Boston being without Jaylen Brown and Derrick White, plus first-half separation like the Clippers
building a big lead over Milwaukee.

[Read more](https://example.com/article-3)

### 4. Warriors' Curry knee setback keeps him out
Stephen Curry has been ruled out for two more games due to his right knee, extending his absence
to at least 25 straight contests. He has progressed to more intense court work but has not yet
cleared a 5-on-5 scrimmage, with Rick Celebrini remaining cautious. Steve Kerr said the return
timetable is running out and requires a green light soon to avoid an inevitable shutdown. Without
Curry, Golden State is 8-15 in his absence and stuck near the 10th seed.

[Read more](https://example.com/article-4)

### 5. Warriors' Moody Gets Successful Patellar Tendon Surgery
Golden State guard Moses Moody underwent successful surgery in Los Angeles to repair a ruptured
left patellar tendon suffered March 23 vs. Dallas. He will miss the rest of the 2025-26 season
and begin rehab immediately, with an update expected during next season's training camp. Moody,
23, averaged career highs this year, including 12.1 points and 40.1% from 3, making his absence
a significant hit to the Warriors' wing depth and spacing.

[Read more](https://example.com/article-5)

### 6. Bucks eliminated after Giannis absence, Spurs blowout
Milwaukee was officially eliminated from playoff contention with a 127-95 blowout loss to the
surging San Antonio Spurs, ending the franchise's streak of nine straight postseason appearances.
Giannis Antetokounmpo missed a sixth straight game with a left knee hyperextension and bone
bruise, contributing to a recent downturn as Stephon Castle posted a triple-double and Victor
Wembanyama added 23 points and 15 rebounds. The loss also tightens the Western race, with the
Spurs moving within two games of first-place Oklahoma City.

[Read more](https://example.com/article-6)

### 7. Jarrett Allen Returns, Cavs Rout Heat 149-128
Jarrett Allen returned from 10 games missed with knee tendinitis and scored 18 points in
18 minutes, helping power Cleveland to a 149-128 regulation win over Miami. Evan Mobley added 23,
James Harden posted 17 points and 14 assists, and Max Strus hit eight 3-pointers as the Cavs set
a franchise regulation scoring record. Allen's return matters because his rim protection and
defensive presence are a key playoff piece for Cleveland.

[Read more](https://example.com/article-7)

### 8. Doncic suspended one game after 16th tech
Luka Doncic received a one-game suspension for picking up his 16th technical foul in the Lakers'
win over Brooklyn. He'll miss Monday's game vs. Washington after double technicals with Ziaire
Williams following a third-quarter jostle. The suspension costs him roughly $264,000 and raises
the stakes for any additional technicals as the regular season tightens.

[Read more](https://example.com/article-8)

### 9. Celtics' Tatum faces usage, leg-confidence questions
Jayson Tatum is back from his torn Achilles after missing the first 62 games, but the early
returns show a careful ramp-up: his usage remains high, he leans heavily on 3-pointers, and
scouts note he may still lack confidence in his leg. The central question for Boston is how to
balance Tatum's desire to resume a first-option role with the near-term reality that he may fit
best as a secondary scorer next to Jaylen Brown while he regains explosiveness.

[Read more](https://example.com/article-9)

### 10. Illinois knocks out Iowa, Final Four berth
Freshman Keaton Wagler scored 25 points as Illinois beat Iowa 71-59, using a decisive frontcourt
advantage to reach the Final Four for the first time since 2005. The Illini out-rebounded Iowa
38-21 in the South Regional final, with David Mirkovic adding 12 rebounds, and they will next
face either Duke or UConn in Indianapolis. The win caps a breakthrough tournament for Brad
Underwood's 28-8 team and highlights Illinois' big-man recruiting pipeline.

[Read more](https://example.com/article-10)
```

---

## 📰 Sources

The current version of the project pulls from:

- **NBA.com Top Stories**
- **ESPN NBA RSS**
- **Selected NBA YouTube channels RSS**

---

## 🧰 Tools Used

This project uses:

- **Python**
- **LangGraph**
- **LangChain**
- **OpenAI**
- **SQLAlchemy**
- **PostgreSQL**
- **BeautifulSoup**
- **feedparser**
- **youtube-transcript-api**
- **Render**

Current models:

- `gpt-5.4-nano`
- `text-embedding-3-small`

---

## 📂 Project Structure

- `app/scrapers` for collecting articles and videos
- `app/steps` for the workflow pipeline
- `app/agents` for summarization, ranking, and email generation
- `app/database` for models and database access
- `app/constants` for prompts, links, and user preferences
- `app/services` for the main workflow entrypoint
- `docker/docker_compose.yaml` for local PostgreSQL
- `render.yaml` for scheduled deployment

---

## 🚀 Running Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose -f docker/docker_compose.yaml up -d
python -m app.services.main
```

---

## 🔐 Environment Variables

Main variables:

- `OPENAI_KEY`
- `DATABASE_URL`
- `MY_EMAIL`
- `APP_PASSWORD`
- `EMAIL_RECIPIENTS`

Optional local database variables:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Optional extras:

- `LOG_LEVEL`
- `LOG_FILE_PATH`
- `PROXY_USERNAME`
- `PROXY_PASSWORD`

If `DATABASE_URL` is missing, the app uses the local `POSTGRES_*` settings instead.

---

## ☁️ Deployment

The project includes [render.yaml](/Users/kuba/NBA%20News%20AI%20Agent/render.yaml) for running the workflow as a daily Render cron job.

---

## 🔧 Future Improvements

- Support multiple users with different profiles
- Add more sources like Twitter, Reddit, and podcasts
- Implement feedback to improve the agent's performance over time
