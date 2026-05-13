function toggleAnswer(btn) {
    const reveal = btn.nextElementSibling;
    if (reveal.style.display === 'none' || reveal.style.display === '') {
        reveal.style.display = 'block';
        btn.textContent = 'Hide Answer';
        btn.classList.add('active');
    } else {
        reveal.style.display = 'none';
        btn.textContent = 'Show Answer';
        btn.classList.remove('active');
    }
}

function toggleSectionAnswers(btn, sectionId) {
    const section = document.getElementById(sectionId);
    const answers = section.querySelectorAll('.answer-reveal');
    const allVisible = Array.from(answers).every(a => a.style.display !== 'none');

    if (allVisible) {
        answers.forEach(a => a.style.display = 'none');
        btn.textContent = 'Show Answers';
        btn.classList.remove('active');
    } else {
        answers.forEach(a => a.style.display = 'block');
        btn.textContent = 'Hide Answers';
        btn.classList.add('active');
    }
}
