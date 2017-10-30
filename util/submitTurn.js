/* 
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

function submitTurn(goal,turn,taskID,workerID,hitId,assignmentId){//,showComplete) {
    // check that all the input us provided
   
    // submit to voiphub
    //
	$.post("submitTurn.py",{mgoal:      JSON.stringify(goal), 
                            turnLog:    JSON.stringify(turn), 
                            taskIdentifier: taskID, 
                            worker:     workerID, 
                            hit:        hitId,
                            assignment: assignmentId},
            function(data) {
                // inform google analytics
		//                try{ pageTracker._trackPageview('/~fj228/G1/submitted'); } catch(err) {}

                // after submiting to voiphub submit to mturk
		
                if (assignmentId != "ASSIGNMENT_ID_NOT_AVAILABLE" &&
                    assignmentId != "None") {

                    var mturk = "https://www.mturk.com/mturk/externalSubmit?"+
                        'assignmentId='+urlencode(assignmentId)+'&'+
                        'xmlFeedback='+urlencode(turn);
                    //var mturk = "https://workersandbox.mturk.com/mturk/externalSubmit?"+
                    //    'assignmentId='+urlencode(assignmentId)+'&'+
                    //    'xmlFeedback='+urlencode(window.log);

                    window.location = mturk;
                }
                else {
                    setTimeout(function(){window.location.reload(true)},1000);
                    //document.getElementById("demo").innerHTML = data;
                }
		
            }
	       );
}


