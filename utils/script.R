library(RSQLite)

con <- dbConnect(dbDriver("SQLite"), dbname='votes.db')
df <- dbReadTable(con, "votes")

for (col in 1:ncol(df))
	df[, col] <- type.convert(df[, col])

df[df$vote == 'Poissa', 4] <- NA
