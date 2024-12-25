from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import happybase
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='spark_process.log'
)

def create_spark_session():
    """Initialize Spark session with HBase configuration"""
    return (SparkSession.builder
            .appName("F1 Data Analysis")
            .config("spark.sql.extensions", "org.apache.spark.sql.hbase")
            .getOrCreate())

def fetch_data_from_hbase(connection, table_name, column_family):
    """Fetch data from HBase and convert to list of dictionaries"""
    table = connection.table(table_name)
    data = []
    
    for key, value in table.scan():
        row_data = {}
        for col, val in value.items():
            cf, qualifier = col.decode('utf-8').split(':')
            if cf == column_family:
                row_data[qualifier] = val.decode('utf-8')
        if row_data:
            row_data['row_key'] = key.decode('utf-8')
            data.append(row_data)
    
    return data

def analyze_driver_performance(spark, connection):
    """Analyze driver performance statistics"""
    logging.info("Starting driver performance analysis")
    
    # Fetch lap data
    lap_data = fetch_data_from_hbase(connection, 'f1_data', 'laps')
    lap_df = spark.createDataFrame(lap_data)
    
    # Calculate average lap times per driver
    avg_lap_times = (lap_df
        .filter(col("lap_duration").isNotNull())
        .groupBy("driver_number")
        .agg(
            avg("lap_duration").alias("avg_lap_time"),
            min("lap_duration").alias("best_lap_time"),
            count("lap_number").alias("total_laps")
        )
        .orderBy("avg_lap_time"))
    
    # Sector performance analysis
    sector_performance = (lap_df
        .filter(
            col("duration_sector_1").isNotNull() &
            col("duration_sector_2").isNotNull() &
            col("duration_sector_3").isNotNull()
        )
        .groupBy("driver_number")
        .agg(
            avg("duration_sector_1").alias("avg_sector1"),
            avg("duration_sector_2").alias("avg_sector2"),
            avg("duration_sector_3").alias("avg_sector3")
        ))
    
    return avg_lap_times, sector_performance

def analyze_telemetry_data(spark, connection):
    """Analyze car telemetry data"""
    logging.info("Starting telemetry data analysis")
    
    # Fetch car data
    car_data = fetch_data_from_hbase(connection, 'f1_data', 'car')
    car_df = spark.createDataFrame(car_data)
    
    # Speed analysis
    speed_analysis = (car_df
        .filter(col("speed").isNotNull())
        .groupBy("driver_number")
        .agg(
            max("speed").alias("top_speed"),
            avg("speed").alias("avg_speed")
        )
        .orderBy(desc("top_speed")))
    
    # DRS usage analysis
    drs_usage = (car_df
        .filter(col("drs").isNotNull())
        .groupBy("driver_number")
        .agg(
            sum(when(col("drs").isin([10, 12, 14]), 1)
                .otherwise(0)).alias("drs_activations")
        )
        .orderBy(desc("drs_activations")))
    
    return speed_analysis, drs_usage

def analyze_pit_stops(spark, connection):
    """Analyze pit stop performance"""
    logging.info("Starting pit stop analysis")
    
    # Fetch pit stop data
    pit_data = fetch_data_from_hbase(connection, 'f1_data', 'pit')
    pit_df = spark.createDataFrame(pit_data)
    
    # Pit stop analysis
    pit_analysis = (pit_df
        .filter(col("pit_duration").isNotNull())
        .groupBy("driver_number")
        .agg(
            avg("pit_duration").alias("avg_pit_time"),
            min("pit_duration").alias("fastest_pit"),
            max("pit_duration").alias("slowest_pit"),
            count("pit_duration").alias("pit_stops")
        )
        .orderBy("avg_pit_time"))
    
    return pit_analysis

def analyze_race_progress(spark, connection):
    """Analyze race progress and positions"""
    logging.info("Starting race progress analysis")
    
    # Fetch position data
    position_data = fetch_data_from_hbase(connection, 'f1_data', 'position')
    position_df = spark.createDataFrame(position_data)
    
    # Position changes analysis
    position_changes = (position_df
        .groupBy("driver_number")
        .agg(
            count(when(col("position") == 1, 1)).alias("laps_led"),
            avg("position").alias("avg_position")
        )
        .orderBy("avg_position"))
    
    return position_changes

def analyze_tyre_strategy(spark, connection):
    """Analyze tyre usage and strategy"""
    logging.info("Starting tyre strategy analysis")
    
    # Fetch stint data
    stint_data = fetch_data_from_hbase(connection, 'f1_data', 'stints')
    stint_df = spark.createDataFrame(stint_data)
    
    # Tyre usage analysis
    tyre_analysis = (stint_df
        .groupBy("driver_number", "compound")
        .agg(
            avg(col("lap_end") - col("lap_start")).alias("avg_stint_length"),
            count("stint_number").alias("number_of_stints")
        )
        .orderBy("driver_number", "compound"))
    
    return tyre_analysis

def save_analysis_results(analyses, output_path):
    """Save analysis results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for name, df in analyses.items():
        # Convert to Pandas for easier saving
        pdf = df.toPandas()
        output_file = f"{output_path}/f1_analysis_{name}_{timestamp}.csv"
        pdf.to_csv(output_file, index=False)
        logging.info(f"Saved {name} analysis to {output_file}")

def main():
    """Main execution function"""
    try:
        # Initialize Spark session
        spark = create_spark_session()
        
        # Connect to HBase
        connection = happybase.Connection('localhost')
        
        # Perform analyses
        analyses = {}
        
        # Driver Performance
        avg_lap_times, sector_performance = analyze_driver_performance(spark, connection)
        analyses['lap_times'] = avg_lap_times
        analyses['sector_performance'] = sector_performance
        
        # Telemetry Analysis
        speed_analysis, drs_usage = analyze_telemetry_data(spark, connection)
        analyses['speed_analysis'] = speed_analysis
        analyses['drs_usage'] = drs_usage
        
        # Pit Stop Analysis
        pit_analysis = analyze_pit_stops(spark, connection)
        analyses['pit_stops'] = pit_analysis
        
        # Race Progress
        position_changes = analyze_race_progress(spark, connection)
        analyses['position_changes'] = position_changes
        
        # Tyre Strategy
        tyre_analysis = analyze_tyre_strategy(spark, connection)
        analyses['tyre_strategy'] = tyre_analysis
        
        # Save results
        save_analysis_results(analyses, "/user/hadoop/f1_analysis")
        
        logging.info("Analysis completed successfully")
        
    except Exception as e:
        logging.error(f"Error during analysis: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()