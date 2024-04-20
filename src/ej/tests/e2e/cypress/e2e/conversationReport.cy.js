describe('Access modal export from reports', () => {
  let conversationId = "";
  
  before(() => {
    cy.registerUser();
  
    cy.url().then(($url) => {
      if($url == `${Cypress.config('baseUrl')}/profile/tour/`) {
        cy.get('form a[hx-post="/profile/tour/?step=skip"]').click()
      }
    })
    cy.createConversation();
    cy.url().then(($url) => {
      // tokens[1] should be the URL conversation id.
      let tokens = $url.match(/.*conversations\/(\d*)\//);
      if (parseInt(tokens[1])) {
        conversationId = tokens[1];
      }
    })
  
    cy.logout();
  });
  
  after(() => {
    cy.removesCypressConversation()
    cy.removesCypressUser();
  });

  it('access export modal from dashboard', () => {
    let conversationUrl = `/cypressmailcom/conversations/${conversationId}/avancos-da-ia-e2e/`;
    let dashboardReportUrl = `/conversations/${conversationId}/avancos-da-ia-e2e/report/data/votes.csv`
    cy.login()
    cy.visit(`${conversationUrl}dashboard/`)
    cy.get('a[class="export-button"]').click()
    cy.get(`a[href="${dashboardReportUrl}"]`)
  });
  
  it('access export modal from comments reports', () => {
    let conversationUrl = `/cypressmailcom/conversations/${conversationId}/avancos-da-ia-e2e/`;
    let commentReportUrl = `/conversations/${conversationId}/avancos-da-ia-e2e/report/data/comments.csv`
    cy.login()
    cy.visit(`${conversationUrl}report/comments/`)
    cy.get('a[class="export-button"]').click()
    cy.get(`a[href="${commentReportUrl}"]`)
  });

  it('access export modal from users reports', () => {
    let conversationUrl = `/cypressmailcom/conversations/${conversationId}/avancos-da-ia-e2e/`;
    let userReportUrl = `/conversations/${conversationId}/avancos-da-ia-e2e/report/data/users.csv`
    cy.login()
    cy.visit(`${conversationUrl}report/users/`)
    cy.get('a[class="export-button"]').click()
    cy.get(`a[href="${userReportUrl}"]`)
  });

})