# Setting path
rm(list=ls())
setwd("/Users/shikharsrivastava/My Drive/Pricing/Pricing_2022/OpCost-Depreciation/")

# Getting input data
dep_data = read.csv("Depreciation_Table.csv",as.is=T)
colnames(dep_data) <- tolower(colnames(dep_data))
op_costs = read.csv("op_costs.csv",as.is=T)
colnames(op_costs) <- tolower(colnames(op_costs))
colnames(op_costs)[2] <- "sub_category"
insurance_cost= read.csv("insurance_unpivoted.csv",as.is=T)
colnames(insurance_cost) <- tolower(colnames(insurance_cost))


# Setting price points to get Ouput for
mkt_price = seq(from = 100, to = 190, by = 10)
mkt_price = c(mkt_price,seq(from = 200, to = 280, by = 20))
mkt_price = c(mkt_price,seq(from = 300, to = 675, by = 25))
mkt_price = c(mkt_price,seq(from = 700, to = 4000, by = 50))

# Creating input file
mkt_p_toadd = rep(mkt_price,dim(dep_data)[1])
dep_data$cat_brand=gsub('"','',dep_data$cat_brand)
input_data = dep_data[rep(seq_len(nrow(dep_data)),length(mkt_price)),]
input_data <- input_data[order(input_data$cat_brand),]
input_data$mkt_price = mkt_p_toadd

## Adding Sub Plans
plans = c(1,3,6,12,18,24)
plans_toadd = rep(plans,dim(input_data)[1])
input_data = input_data[rep(seq_len(nrow(input_data)),length(plans)),]
input_data <- input_data[order(input_data$cat_brand,input_data$mkt_price),]
input_data$plans = plans_toadd

## Adding Op Costs
input_data = merge(input_data,op_costs[,c('sub_category','op_costs_eur')],by="sub_category")



## Getting correct insurance cost
library(sqldf)
input_data = sqldf("
  SELECT d1.*,d2.value*d1.plans insurance_cost
  FROM input_data d1 JOIN insurance_cost d2
  ON d1.category = d2.category
  WHERE d1.mkt_price>=d2.price_from
  AND d1.mkt_price<d2.price_to
  ORDER BY cat_brand,mkt_price,plans
",)

## Imputing na values
input_data[is.na(input_data)]<-0

## Calculating Depreciation for the plan
input_data$dep_cost = input_data$mkt_price/input_data$depreciation_months*input_data$plans

## Calculating other costs
input_data$interest_cost = input_data$mkt_price * 0.06/12* 0.95 * (1-6/input_data$depreciation_months) * input_data$plans


input_data$impairment_cost = input_data$mkt_price * 0.0525/12 * input_data$plans

input_data[is.na(input_data)] <- 0
colnames(input_data)[10] <- "insurance_cost"

input_data$costs = input_data$op_costs_eur + input_data$insurance_cost + input_data$dep_cost + input_data$impairment_cost + input_data$interest_cost



# Setting up %Mkt Price boundaries
input_data$pp_LowerBoundary = ifelse(input_data$plans == 1,0.107,
																	ifelse(input_data$plans == 3, 0.078,
																		ifelse(input_data$plans == 6, 0.058,
																			ifelse(input_data$plans==  12, 0.049,
																				ifelse(input_data$plans == 18, 0.043,
																					ifelse(input_data$plans==  24, 0.038,99
																		))))))
input_data$pp_UpperBoundary = ifelse(input_data$plans == 1,0.135,
																	ifelse(input_data$plans==  3, 0.095,
																		ifelse(input_data$plans == 6, 0.085,
																			ifelse(input_data$plans==  12, 0.065,
																				ifelse(input_data$plans==  18, 0.051,
																					ifelse(input_data$plans == 24, 0.0405,99
																		))))))


input_data$pp_ideal = ifelse(input_data$plans == 1,0.108,
																	ifelse(input_data$plans==  3, 0.08,
																		ifelse(input_data$plans == 6, 0.062,
																			ifelse(input_data$plans==  12, 0.051,
																				ifelse(input_data$plans==  18, 0.046,
																					ifelse(input_data$plans == 24, 0.039,99
																		))))))

input_data$pp_maximum = ifelse(input_data$plans == 1,0.3,
																	ifelse(input_data$plans==  3, 0.16,
																		ifelse(input_data$plans == 6, 0.12,
																			ifelse(input_data$plans==  12, 0.068,
																				ifelse(input_data$plans==  18, 0.051,
																					ifelse(input_data$plans == 24, 0.0405,99
																		))))))


# Getting charm price points
price_scales = read.csv("price_scales.csv",as.is=T)



#### i = 100
#### cost = input_data$costs[i]
#### plan = input_data$plans[i]
#### mkt_price = input_data$mkt_price[i]
#### min_value = input_data$pp_LowerBoundary[i]*mkt_price
#### max_value = input_data$pp_UpperBoundary[i]*mkt_price
####
#### price_scales_subset = price_scales[price_scales$Price>=min_value,]
#### price_scales_subset = price_scales_subset[price_scales_subset$Price<=max_value,]
#### price_scales_subset$margin = 0.957 - cost/(price_scales_subset$Price*plan)


# Creating final input file
dt_input = input_data[,c('sub_category','category','brand','cat_brand','mkt_price','plans','costs','pp_ideal','pp_maximum','pp_LowerBoundary','pp_UpperBoundary')]

library(reshape2)

# Creating Margin Function
margin_filter <- function(price_array,cost,plan,margin_limit_array) {
	plan_array = rep(plan,length(price_array))
	cost_array = rep(cost,length(price_array))
  margin = 0.957 - cost_array/(price_array*plan_array)  ## taking into account payment and collection costs. 
  for (margin_limit in margin_limit_array){
  	x = price_array[margin>=margin_limit]
  	if (length(x)>0){
  		break
  	}
  }
  if(length(x)>0){
  	x
  }else{max(price_array)}
}


# Running for loop for each category and brand combination
for (cb in unique(dt_input$cat_brand)){
	dt_todo = dt_input[dt_input$cat_brand==cb,]
	# Running for loop for each mkt price
	for (mp in unique(dt_todo$mkt_price)){
		dt_todo_fin = dt_todo[dt_todo$mkt_price==mp,]
		dt_tpose = dcast(data = dt_todo_fin, formula = category+sub_category+brand+cat_brand+mkt_price ~ plans, fun.aggregate = mean, value.var = "costs")
		colnames(dt_tpose)[6:11] <- paste0("cost_",colnames(dt_tpose)[6:11],"m")
		cost = dt_todo_fin$costs
		plan = dt_todo_fin$plans
		mkt_price = dt_todo_fin$mkt_price
		# min_value = dt_todo_fin$pp_LowerBoundary[Leader]*mkt_price
		# max_value = dt_todo_fin$pp_UpperBoundary[Leader]*mkt_price

		pp_ideal = dt_todo_fin$pp_ideal
		ideal_values = dt_todo_fin$pp_ideal*mkt_price
		max_values = dt_todo_fin$pp_maximum*mkt_price
		lb_values = dt_todo_fin$pp_LowerBoundary*mkt_price
		ub_values = dt_todo_fin$pp_UpperBoundary*mkt_price

		new_values=c()
		for (i in ideal_values){
			new_values = c(new_values,min(price_scales[price_scales$Price>=i,2]))
		}

		new_max_values=c()
		for (i in max_values){
			new_max_values = c(new_max_values,max(price_scales[price_scales$Price<=i,2],if.na=3.9))
		}
		new_values[which(new_max_values<new_values)]<-new_max_values[which(new_max_values<new_values)]

		new_lb_values=c()
		for (i in lb_values){
			new_lb_values = c(new_lb_values,min(price_scales[price_scales$Price>=i,2]))
		}
		new_lb_values[which(new_max_values<new_lb_values)]<-new_max_values[which(new_max_values<new_lb_values)]


		new_ub_values=c()
		for (i in ub_values){
			new_ub_values = c(new_ub_values,max(price_scales[price_scales$Price<=i,2],if.na=3.9))
		}
		new_ub_values[which(new_ub_values<new_lb_values)]<-new_lb_values[which(new_ub_values<new_lb_values)]
		new_ub_values[which(new_max_values<new_ub_values)]<-new_max_values[which(new_max_values<new_ub_values)]


		margin = 0.957 - cost/(new_values*plan)
		max_margin = 0.957 - cost/(new_max_values*plan)
		lb_margin = 0.957 - cost/(new_lb_values*plan)
		ub_margin = 0.957 - cost/(new_ub_values*plan)


		margin_limit_array = c(0.20,0.15,0.10,0.05,0.01)
		if (any(max_margin[1:4]<0) ){			#| any(ub_margin[1:4]<0
			values = new_max_values; margin = max_margin; pp=dt_todo_fin$pp_maximum
			names(values) <- c('price_1m','price_3m','price_6m','price_12m','price_18m','price_24m')
			names(margin) <- c('margin_1m','margin_3m','margin_6m','margin_12m','margin_18m','margin_24m')
			names(pp) <- c('pp_1m','pp_3m','pp_6m','pp_12m','pp_18m','pp_24m')
			final_out = cbind(cbind(cbind(unique(dt_todo_fin[c('sub_category','category','brand','cat_brand','mkt_price')]),t(as.data.frame(values))),t(as.data.frame(pp))),t(as.data.frame(margin)))
			}else{
			searchspace_1m <- subset(price_scales , Price <= new_max_values[1] & Price >= new_lb_values[1])[,'Price']
			ss_1m <- margin_filter(searchspace_1m,cost[1],1,margin_limit_array)
			searchspace_3m <- subset(price_scales , Price <= new_max_values[2] & Price >= new_lb_values[2])[,'Price']
			ss_3m <- margin_filter(searchspace_3m,cost[2],plan[2],margin_limit_array)
			searchspace_6m <- subset(price_scales , Price <= new_max_values[3] & Price >= new_lb_values[3])[,'Price']
			ss_6m <- margin_filter(searchspace_6m,cost[3],plan[3],margin_limit_array)
			searchspace_12m <- subset(price_scales , Price <= new_max_values[4] & Price >= new_lb_values[4])[,'Price']
			ss_12m <- margin_filter(searchspace_12m,cost[4],plan[4],margin_limit_array)
			searchspace_18m <- subset(price_scales , Price <= new_max_values[5] & Price >= new_lb_values[5])[,'Price']
			ss_18m <- margin_filter(searchspace_18m,cost[5],plan[5],margin_limit_array)
			searchspace_24m <- subset(price_scales , Price <= new_max_values[6] & Price >= new_lb_values[6])[,'Price']
			ss_24m <- margin_filter(searchspace_24m,cost[6],plan[6],margin_limit_array)

			ss_matrix = expand.grid(ss_1m=ss_1m,ss_3m=ss_3m,ss_6m=ss_6m,ss_12m=ss_12m,ss_18m=ss_18m,ss_24m=ss_24m)
			ss_matrix = subset(ss_matrix,ss_1m>ss_3m & ss_3m>ss_6m & ss_6m>ss_12m & ss_12m>ss_18m & ss_12m>ss_24m)
			if (dim(ss_matrix)[1]==0) next


			ss_matrix = cbind(ss_matrix,ss_matrix/mkt_price)
			colnames(ss_matrix)[7:12] <- gsub("ss","pp",colnames(ss_matrix)[7:12])
			weights <- c("1m"=200, "3m"=200, "6m"=300, "12m"=500, "18m"=10, "24m"=5)
			plans_name <- c("1m", "3m", "6m", "12m", "18m", "24m")
			ss_matrix$cost = rowSums(t(t(abs(sweep(ss_matrix[7:12], 2, pp_ideal, "-"))) * weights[plans_name])) # Optimization function
			final_out = ss_matrix[which.min(ss_matrix$cost),] # Optimization function
			final_out = final_out[1,] # Optimization function
			final_out$mkt_price = unique(mkt_price)
			margin_toadd = 0.957 - cost/(final_out[1:6]*plan)
			names(margin_toadd) <- gsub('ss','margin',names(margin_toadd))
			final_out$cost <- NULL
			final_out = cbind(final_out,unique(dt_todo[,c('sub_category','category','brand','cat_brand')]))
			final_out = cbind(final_out,as.data.frame(margin_toadd))
			colnames(final_out)[1:6] <- gsub('ss','price',colnames(final_out)[1:6])
			final_out = final_out[,c('sub_category','category','brand','cat_brand','mkt_price',colnames(final_out)[c(1:12,18:23)])]
			
		}
		# write.table(final_out, "price_fit.csv", sep = ",", col.names = !file.exists("price_fit.csv"), append = T,row.names=F)
		if (cb=='2-in-1 laptops' & mp==100){
			output = final_out
		} else {
			output=rbind(output,final_out)
		}
	}
}

write.csv(output,'price_fit_V3_2.csv',row.names=F)



a=read.csv('price_fit_V3_2.csv',as.is=T)










