python tts_cli.py --text "A viral post claims that Donald Trump’s proposed twentytwentyfive tax cuts could eliminate federal income tax for anyone earning under two hundred thousand dollars. Supporters believe this might boost disposable income, leading to a rise in crypto investments. The post highlights XRP as a potential frontrunner, thanks to its fast transactions, low fees, Ripple’s legal momentum, and the chance of an ETF approval. It even suggests XRP could become a store of value and jump a thousand percent in price—though that depends entirely on this tax policy becoming real. Do you think a tax cut like this could actually reshape the crypto market?"  --gender female --pitch low --seed 42567 --speed very_high

build image 

docker build -t spark-tts . --no-cache


