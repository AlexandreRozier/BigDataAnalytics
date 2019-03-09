package requester;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Logger;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Date;
import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Created with Intellij IDEA.
 * User: Nursultan
 * Date: 12/09/18
 * Time: 6:26 PM
 */

public class Program {
    public static Logger logger = Logger.getLogger(Program.class);
    static String  ip = "https://54.147.181.67";
    private static HttpHandler[] httpHandlers;
    private static HttpHandler[] httpAnomalyHandlers;
    private static int threadCount = 40;
    private static int anomalyThreadCount = 40;
    private static long lastAnomalyTime = 0;

    /**
     * True - the project will be compiled with an anomaly service
     * False - the project will be compiled as a service for normal data production
     * */
    private static boolean isAnomalyService = false;

    public static void main(String[] args) {
        logger.info("Started!");
        BasicConfigurator.configure();

        if (isAnomalyService){
            produceAnomaly();
        } else{
            produceData();
        }
    }

    //region produceData
    /**
     * multiple threads send requests to produce a smooth pattern of data
     */
    private static void produceData(){
        httpHandlers = new HttpHandler[threadCount];

        try {
            for (int i=0; i<threadCount; i++){
                httpHandlers[i] = new HttpHandler(new Integer(i), logger, false);
                httpHandlers[i].start();
            }
        }
        catch (Exception ex)
        {
            logger.error(ex.getMessage());
        }
    }
    //endregion

    //region produceAnomaly
    /**
     * multiple threads send a bunch of requests in a short period of time
     */
    private static void produceAnomaly(){
        while (true){
            try{
                Thread.sleep(1000);

                //every 12 hours
                if ( (System.currentTimeMillis() - lastAnomalyTime)>(12*3600*1000)){

                    lastAnomalyTime = System.currentTimeMillis();

                    //generate one anomaly within 12 hours
                    Random rand = new Random();
                    int random = rand.nextInt(12*3600*1000) + 1;
                    logger.info("Random = " + random);
                    Thread.sleep(random);

                    logger.info("Anomaly has been started: " + System.currentTimeMillis()/1000);
                    httpAnomalyHandlers = new HttpHandler[anomalyThreadCount];

                    for (int i=0; i<anomalyThreadCount; i++){
                        httpAnomalyHandlers[i] = new HttpHandler(new Integer(i), logger, true);
                        httpAnomalyHandlers[i].start();
                    }

                    long sleepingTime = 12*3600*1000 - random;
                    logger.info("Sleeping time: " + sleepingTime/1000);
                    Thread.sleep(sleepingTime);
                }
            }
            catch (InterruptedException ex){
                logger.error(ex.getMessage());
            }
        }
    }
    //endregion

    //region produceAnomalyOld2
    private static void produceAnomalyOld2(){
        while (true){
            try{
                Thread.sleep(1000);

                ZoneId zoneId = ZoneId.of("UTC");
                ZonedDateTime now = ZonedDateTime.now();
                long nowSeconds = now.toInstant().getEpochSecond();
                ZonedDateTime nextDay = now.plusDays(1);
                ZonedDateTime nextDayMidnight = nextDay.toLocalDate().atStartOfDay(zoneId);
                long endOfTheDaySeconds = nextDayMidnight.toInstant().getEpochSecond();
                long leftSeconds = endOfTheDaySeconds - nowSeconds;

                //generate anomaly time (in seconds)
                long random1 = ThreadLocalRandom.current().nextLong(1, leftSeconds);
                Thread.sleep(random1);



                long random2 = 0;
                if (random1 < leftSeconds ){
                     random2 = ThreadLocalRandom.current().nextLong(random1, endOfTheDaySeconds);
                }



            }
            catch (InterruptedException ex){
                logger.error(ex.getMessage());
            }
        }
    }
    //endregion

    //region getCurrentHour
    private static int getCurrentHour(){
        Date date = new Date(System.currentTimeMillis());
        DateFormat df2 = new SimpleDateFormat("HH:mm:ss");
        String[] strTime = df2.format(date).split(":");
        int hour = Integer.parseInt(strTime[0]);

        return hour;
    }
    //endregion
}
