'use strict';
console.log('Loading function2');
const https = require('https');
const axios = require('axios');
exports.handler = (event, context, callback) => {
    let success = 0;
    let failure = 0;
    const url  = process.env['SLACK_URL'];
    const output = event.records.map((record) => {
        /* Data is base64 encoded, so decode here */
        const recordData = Buffer.from(record.data, 'base64');
        try {
            /*
             * Note: Write logic here to deliver the record data to the
             * destination of your choice
             */
            const slackMessage = {
                record: record,
                recordData: recordData,
            };
            const request = {
                text: JSON.stringify(slackMessage),
                username: "medium_bot",
            } 
            const sendToSlack = false;  // SET TO TRUE, TO SEE MESSAGE IN SLACK
            if(sendToSlack) {
                axios.post(url, request).then(response => { 
                	console.log(response);
                })
                .catch(error => {
                    console.log('AXIOS ERROR:');
                    console.log(error.response);
                });
            }

            success++;
            return {
                recordId: record.recordId,
                result: 'Ok',
            };
        } catch (err) {
            failure++;
            return {
                recordId: record.recordId,
                result: 'DeliveryFailed',
            };
        }
    });
    console.log(`Successful delivered records ${success}, Failed delivered records ${failure}.`);
    callback(null, {
        records: output,
    });
};
