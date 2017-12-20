pkgTest <- function(x)
{
  if (!require(x,character.only = TRUE))
  {
    install.packages(x,repos = "http://cran.us.r-project.org")
    if(!require(x,character.only = TRUE)) stop("Package not found")
  }
}
#https://jonkimanalyze.wordpress.com/2014/03/25/ggplot2-time-series-axis-control-breaks-label-limitshttpsjonkimanalyze-wordpress-comwp-adminedit-phpinline-edit/
pkgTest("plyr")
library("plyr")
pkgTest("ggplot2")
library("ggplot2")
pkgTest("scales")
library("scales")

test_data<- read.csv("out5.csv")
test_data$hour = as.POSIXct(test_data$Date,format="%Y-%m-%d %H:%M:%OS")
hits = count(test_data, vars = c("hour","Message.ID"))
ggplot(data=hits) + geom_histogram(aes(x=hour), bins=24*4) + xlab("Temps") + ylab("Number of messages") + labs(title="Messages exchanges") + scale_x_datetime(breaks = date_breaks("1 month"))