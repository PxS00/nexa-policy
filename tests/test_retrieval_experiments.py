from src.retrieval_experiment import split_question
from src.hybrid_experiment import tokens, lexical_results
from src.models import SearchResult


def test_split_preserves_question_when_more_than_three_parts():
    question = 'Onde consultar férias e qual teto de hotel e como pedir acessos e onde denunciar?'
    assert split_question(question) == [question]


def test_split_keeps_compound_terms_without_question_word():
    assert split_question('O que é segurança e privacidade?') == ['O que é segurança e privacidade?']


def test_lexical_normalizes_accents_and_requires_two_content_terms():
    assert tokens('Qual a EDUCAÇÃO?') == {'educacao'}
    one = SearchResult('educação', {'source_path':'one'}, .1)
    two = SearchResult('educação anual', {'source_path':'two'}, .2)
    assert lexical_results('Qual educação anual?', [one,two]) == [two]
