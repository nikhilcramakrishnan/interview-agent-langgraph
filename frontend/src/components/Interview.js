import React, { useState } from 'react';
import { useInterview } from '../context/InterviewContext';
import { submitAnswer } from '../api';
import {
  Container,
  TextField,
  Typography,
  Box,
  AppBar,
  Toolbar,
  Paper,
  Grid,
} from '@mui/material';
import { LoadingButton } from '@mui/lab';

export default function Interview() {
  const { sessionId, interviewData, updateInterviewData } = useInterview();
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  if (!sessionId) {
    return (
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Interview Application
            </Typography>
          </Toolbar>
        </AppBar>
        <Container sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="h6">
            No active interview session. Please start a new interview.
          </Typography>
        </Container>
      </Box>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answer.trim()) {
      alert('Please enter an answer.');
      return;
    }

    setLoading(true);
    try {
      const response = await submitAnswer(sessionId, answer);
      updateInterviewData(response);
      setAnswer('');
    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Failed to submit answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const hasQuestion = interviewData && interviewData.current_question;
  const isInterviewOver = interviewData && interviewData.overall_score != null;

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Interview Session
          </Typography>
          {isInterviewOver && (
            <Typography variant="h6">
              Final Score: {interviewData.overall_score}
            </Typography>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 4 }}>
              {hasQuestion ? (
                <>
                  <Typography variant="h6" gutterBottom>
                    {interviewData.current_question.text}
                  </Typography>
                  <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
                    <TextField
                      label="Your Answer"
                      variant="outlined"
                      fullWidth
                      multiline
                      rows={10}
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      disabled={loading}
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                      <LoadingButton
                        variant="contained"
                        type="submit"
                        size="large"
                        loading={loading}
                        disabled={!answer.trim() || loading}
                      >
                        Submit Answer
                      </LoadingButton>
                    </Box>
                  </Box>
                </>
              ) : isInterviewOver ? (
                <Typography variant="h5" color="primary" align="center">
                  Interview Completed!
                </Typography>
              ) : (
                <Typography variant="h6" align="center">
                  Loading next question...
                </Typography>
              )}
            </Paper>

         
        </Grid>
        <Grid item xs={12} md={4} mt={5}>
            <Paper elevation={3} sx={{ p: 3, bgcolor: 'grey.50' }}>
              <Typography variant="h6" gutterBottom>
                Feedback
              </Typography>
              {interviewData?.feedback ? (
                <Typography variant="body1">
                  {interviewData.feedback}
                </Typography>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  No feedback yet.
                </Typography>
              )}
            </Paper>
          </Grid>
      </Container>
    </Box>
  );
}
