package requester;

import java.io.DataOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import org.apache.log4j.Logger;

/**
 * Created with Intellij IDEA.
 * User: Nursultan
 * Date: 12/09/18
 * Time: 6:26 PM
 */

public class HttpHandler extends Thread {
    private String  ip = "https://54.147.181.67";
    private Integer threadNo;
    private final Logger logger;
    private int requestCount = 0;
    private boolean isAnomaly = false;

    public HttpHandler(Integer _threadNumber, Logger _logger, boolean _isAnomaly){
        threadNo = _threadNumber;
        logger = _logger;
        isAnomaly = _isAnomaly;
    }

    @Override
    public void run() {
        while(true) {
            sendRequests();
            requestCount++;

            if (!isAnomaly){
                if (requestCount%10 == 0){
                    try {
                        Thread.sleep(2000);
                    }
                    catch (InterruptedException ex){
                        logger.info(ex.getMessage());
                    }

                }
            }

            if (isAnomaly && requestCount >= 300000){
                break;
            }
        }
    }

    private void sendRequests(){
        try{
            URL obj = new URL(ip);
            HttpURLConnection connection = (HttpURLConnection) obj.openConnection();
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type",
                    "application/x-www-form-urlencoded");

            connection.setRequestProperty("Content-Language", "en-US");
            connection.setUseCaches(false);
            connection.setDoOutput(true);
            connection.setDoOutput(true);

            //Send request
            DataOutputStream wr = new DataOutputStream (connection.getOutputStream());

            if (isAnomaly){
                wr.writeBytes("a");
            }else{
                wr.writeBytes("");
            }

            wr.flush();
            wr.close();

            int responseCode = connection.getResponseCode();
            logger.info(threadNo.toString() +  " POSTed with response code " + responseCode);
        }
        catch (Exception ex)
        {
            if (requestCount%100000 == 0){
                logger.error(ex.getMessage() + " " + requestCount);
            }
        }
    }
}
