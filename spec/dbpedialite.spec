require File.dirname(__FILE__) + "/spec_helper.rb"
require 'dbpedialite'


## Note: these are integration tests. Mocking is done at the HTTP request level.

set :environment, :test

describe 'dbpedia lite' do
  include Rack::Test::Methods

  def app
    DbpediaLite
  end

  context "GETing the homepage" do
    context "in a non-production environment" do
      before :each do
        get '/'
      end

      it "should be successful" do
        last_response.should be_ok
      end

      it "should be of type text/html" do
        last_response.content_type.should == 'text/html;charset=utf-8'
      end

      it "should be cachable" do
        last_response.headers['Cache-Control'].should =~ /max-age=([1-9]+)/
      end

      it "should contain the readme text" do
        last_response.body.should =~ /takes some of the structured data/
      end
    end

    context "in a production environment" do
      before :each do
        set :environment, :production
        get '/'
      end

      after :each do
        set :environment, :test
      end

      it "should redirect" do
        last_response.status.should == 301
        last_response.headers['Location'].should == 'http://dbpedialite.org/'
      end
    end
  end

  context "GETing a search page with a query string" do
    before :each do
      FakeWeb.register_uri(:get, %r[http://en.wikipedia.org/w/api.php], :body => fixture_data('search-rat.json'))
      get '/search?term=rat'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be text/html" do
      last_response.content_type.should == 'text/html;charset=utf-8'
    end

    it "should contain an escaped link to a title page" do
      last_response.body.should =~ %r[<a href=\"/titles/Brown_rat\">Brown rat</a>]
    end

    it "should contain snippets" do
      last_response.body.should =~ %r[The brown <span class='searchmatch'>rat</span>]
    end
  end

  context "GETing a search page with a query string (from jquery autocomplete)" do
    before :each do
      FakeWeb.register_uri(:get, %r[http://en.wikipedia.org/w/api.php], :body => fixture_data('search-rat.json'))
      get '/search.json?term=rat'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be text/json" do
      last_response.content_type.should == 'text/json;charset=utf-8'
    end

    it "should contain the search term" do
      last_response.body.should =~ %r[Rat]
    end
  end

  context "GETing the search page for unsupport format" do
    before :each do
      FakeWeb.register_uri(:get, %r[http://en.wikipedia.org/w/api.php], :body => fixture_data('search-rat.json'))
      get '/search.ratrat?term=rat'
    end

    it "should return a 400 error" do
      last_response.should be_client_error
    end

    it "should include the text 'Unsupported format' in the body" do
      last_response.body.should =~ /Unsupported format/i
    end
  end

  context "GETing the search page without a query string" do
    before :each do
      get '/search'
    end

    it "should be a redirect" do
      last_response.should be_redirect
    end

    it "should set the location header to redirect to /" do
      last_response.location.should == 'http://example.org/'
    end
  end

  context "GETing a title URL" do
    before :each do
      FakeWeb.register_uri(:get, %r[http://en.wikipedia.org/w/api.php], :body => fixture_data('query-u2.json'))
      get '/titles/U2'
    end

    it "should be a redirect" do
      last_response.should be_redirect
    end

    it "should set the location header to redirect to /" do
      last_response.location.should == 'http://example.org/things/52780'
    end

    it "should be cachable" do
      last_response.headers['Cache-Control'].should =~ /max-age=([1-9]+)/
    end
  end

  context "GETing an invalid title URL" do
    before :each do
      FakeWeb.register_uri(:get, %r[http://en.wikipedia.org/w/api.php], :body => fixture_data('query-zsefpfs.json'))
      get '/titles/zsefpfs'
    end

    it "should return 404 Not Found" do
      last_response.should be_not_found
    end
  end

  context "GETing an HTML page for a geographic thing" do
    before :each do
      FakeWeb.register_uri(:get,
                           'http://en.wikipedia.org/wiki/index.php?curid=934787',
                           :body => fixture_data('ceres.html'),
                           :content_type => 'text/html; charset=UTF-8'
                           )
      FakeWeb.register_uri(:get,
                           %r[http://www.freebase.com/api/service/mqlread],
                           :body => fixture_data('freebase-mqlread-ceres.json')
                           )
      header "Accept", "text/html"
      get '/things/934787'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be of type text/html" do
      last_response.content_type.should == 'text/html;charset=utf-8'
    end

    it "should be cachable" do
      last_response.headers['Cache-Control'].should =~ /max-age=([1-9]+)/
    end

    it "should contain an abstract for the thing" do
      last_response.body.should =~ /<p>Ceres is a village in Fife, Scotland/
    end

    it "should have a Google Map on the page" do
      last_response.body.should =~ %r[<div id="map"></div>]
    end

    it "should include the title of the thing in the page title" do
      last_response.body.should =~ %r[<title>dbpedia lite - Ceres, Fife</title>]
    end

    it "should include a <meta> description tag with a truncated abstract" do
      last_response.body.should =~ %r[<meta name="description" content="Ceres is a village in Fife, Scotland]
    end

    it "should have the title of the thing as RDFa" do
      rdfa_graph.should have_triple([
                                     RDF::URI("http://dbpedialite.org/things/934787#thing"),
                                     RDF::RDFS.label,
                                     RDF::Literal("Ceres, Fife")
                                    ])
    end

    it "should have a link to the Wikipedia page in the RDFa" do
      rdfa_graph.should have_triple([
                                     RDF::URI("http://dbpedialite.org/things/934787#thing"),
                                     RDF::FOAF.isPrimaryTopicOf,
                                     RDF::URI("http://en.wikipedia.org/wiki/Ceres%2C_Fife"),
                                    ])
    end

    it "should have a link to an external link in the RDFa" do
      rdfa_graph.should have_triple([
                                     RDF::URI("http://dbpedialite.org/things/934787#thing"),
                                     RDF::FOAF.page,
                                     RDF::URI("http://www.fife.50megs.com/ceres-history.htm"),
                                    ])
    end

    it "should have an RDFa triple linking the document to the thing" do
      rdfa_graph.should have_triple([
                                     RDF::URI("http://dbpedialite.org/things/934787"),
                                     RDF::FOAF.primaryTopic,
                                     RDF::URI("http://dbpedialite.org/things/934787#thing"),
                                    ])
    end

    it "should have an dc:modified RDFa triple for the document" do
      rdfa_graph.should have_triple([
                                     RDF::URI("http://dbpedialite.org/things/934787"),
                                     RDF::URI("http://purl.org/dc/terms/modified"),
                                     RDF::Literal('2010-04-29T10:22:00Z')
                                    ])
    end

    it "should have an RDFa triple linking the altenate RDF/XML format" do
      rdfa_graph.should have_triple([
                                     RDF::URI("http://dbpedialite.org/things/934787"),
                                     RDF::URI("http://www.w3.org/1999/xhtml/vocab#alternate"),
                                     RDF::URI("http://dbpedialite.org/things/934787.rdf"),
                                    ])
    end

  end

  context "GETing an HTML thing page for a thing that doesn't exist" do
    before :each do
      FakeWeb.register_uri(:get, %r[http://en.wikipedia.org/wiki/index.php], :body => fixture_data('notfound.html'))
      get '/things/504825766'
    end

    it "should return 404 Not Found" do
      last_response.should be_not_found
    end

    it "should include the text 'Thing Not Found' in the body" do
      last_response.body.should =~ /Thing Not Found/i
    end
  end

  context "GETing an unsupport format for a thing" do
    before :each do
      FakeWeb.register_uri(:get,
                           'http://en.wikipedia.org/wiki/index.php?curid=934787',
                           :body => fixture_data('ceres.html'),
                           :content_type => 'text/html; charset=UTF-8'
                           )
      FakeWeb.register_uri(:get,
                           %r[http://www.freebase.com/api/service/mqlread],
                           :body => fixture_data('freebase-mqlread-ceres.json')
                           )
      get '/things/934787.ratrat'
    end

    it "should return a 400 error" do
      last_response.should be_client_error
    end

    it "should include the text 'Unsupported format' in the body" do
      last_response.body.should =~ /Unsupported format/i
    end
  end

  context "GETing an N-Triples page for a geographic thing" do
    before :each do
      FakeWeb.register_uri(:get,
                           'http://en.wikipedia.org/wiki/index.php?curid=934787',
                           :body => fixture_data('ceres.html'),
                           :content_type => 'text/html; charset=UTF-8'
                           )
      FakeWeb.register_uri(:get,
                           %r[http://www.freebase.com/api/service/mqlread],
                           :body => fixture_data('freebase-mqlread-ceres.json')
                           )
      header "Accept", "text/plain"
      get '/things/934787'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be of type text/plain" do
      last_response.content_type.should == 'text/plain;charset=utf-8'
    end

    it "should be cachable" do
      last_response.headers['Cache-Control'].should =~ /max-age=([1-9]+)/
    end
  end

  context "GETing an JSON page for a geographic thing" do
    before :each do
      FakeWeb.register_uri(:get,
                           'http://en.wikipedia.org/wiki/index.php?curid=934787',
                           :body => fixture_data('ceres.html'),
                           :content_type => 'text/html; charset=UTF-8'
                           )
      FakeWeb.register_uri(:get,
                           %r[http://www.freebase.com/api/service/mqlread],
                           :body => fixture_data('freebase-mqlread-ceres.json')
                           )
      header "Accept", "application/json"
      get '/things/934787'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be of type application/json" do
      last_response.content_type.should == 'application/json'
    end

    it "should be cachable" do
      last_response.headers['Cache-Control'].should =~ /max-age=([1-9]+)/
    end
  end

  context "GETing an N3 page for a geographic thing" do
    before :each do
      FakeWeb.register_uri(:get,
                           'http://en.wikipedia.org/wiki/index.php?curid=934787',
                           :body => fixture_data('ceres.html'),
                           :content_type => 'text/html; charset=UTF-8'
                           )
      FakeWeb.register_uri(:get,
                           %r[http://www.freebase.com/api/service/mqlread],
                           :body => fixture_data('freebase-mqlread-ceres.json')
                           )
      header "Accept", "text/n3"
      get '/things/934787'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be of type text/n3" do
      last_response.content_type.should == 'text/n3;charset=utf-8'
    end

    it "should be cachable" do
      last_response.headers['Cache-Control'].should =~ /max-age=([1-9]+)/
    end
  end

  context "GETing an RDF/XML page for a geographic thing by content negotiation" do
    before :each do
      FakeWeb.register_uri(:get,
                           'http://en.wikipedia.org/wiki/index.php?curid=934787',
                           :body => fixture_data('ceres.html'),
                           :content_type => 'text/html; charset=UTF-8'
                           )
      FakeWeb.register_uri(:get,
                           %r[http://www.freebase.com/api/service/mqlread],
                           :body => fixture_data('freebase-mqlread-ceres.json')
                           )
      header "Accept", "application/rdf+xml"
      get '/things/934787'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be of type application/rdf+xml" do
      last_response.content_type.should == 'application/rdf+xml'
    end

    it "should be cachable" do
      last_response.headers['Cache-Control'].should =~ /max-age=([1-9]+)/
    end

    it "should contain the URI of the document we requested" do
      last_response.body.should =~ %r[<ns0:Document rdf:about="http://example.org/things/934787">]
    end
  end

  context "GETing an RDF/XML page for a geographic thing by suffix" do
    before :each do
      FakeWeb.register_uri(:get,
                           'http://en.wikipedia.org/wiki/index.php?curid=934787',
                           :body => fixture_data('ceres.html'),
                           :content_type => 'text/html; charset=UTF-8'
                           )
      FakeWeb.register_uri(:get,
                           %r[http://www.freebase.com/api/service/mqlread],
                           :body => fixture_data('freebase-mqlread-ceres.json')
                           )
      header "Accept", "text/plain"
      get '/things/934787.rdf'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be of type application/rdf+xml" do
      last_response.content_type.should == 'application/rdf+xml'
    end

    it "should contain the URI of the document we requested" do
      last_response.body.should =~ %r[<ns0:Document rdf:about="http://example.org/things/934787.rdf">]
    end
  end

  context "GETing the gems information page" do
    before :each do
      get '/gems'
    end

    it "should be successful" do
      last_response.should be_ok
    end

    it "should be of type text/html" do
      last_response.content_type.should == 'text/html;charset=utf-8'
    end

    it "should include a summary for the Sinatra gem" do
      last_response.body.should =~ /Classy web-development dressed in a DSL/
    end
  end

  context "extracting vocabularies" do
    before :each do
      @graph = RDF::Graph.new do |g|
        g << [RDF::URI('http://a.com/'), RDF::DC.title, "A"]
        g << [RDF::URI('http://b.com/'), RDF::FOAF.name, "B"]
        g << [RDF::URI('http://c.com/'), RDF::FOAF.nick, "C"]
      end
      @vocabularies = app.extract_vocabularies(@graph)
    end

    it "should extract 2 vocabularies" do
      @vocabularies.length.should == 2
    end

    it "should have a key for the FOAF vocabulary" do
      @vocabularies.should have_key :foaf
    end

    it "should have a key for the FOAF vocabulary" do
      @vocabularies.should have_key :foaf
    end

    it "should have the right namespace the FOAF vocabulary" do
      @vocabularies[:foaf].should == RDF::FOAF
    end

    it "should have the right namespace the DC vocabulary" do
      @vocabularies[:dc].should == RDF::DC
    end
  end

  def rdfa_graph
    base_uri = "http://dbpedialite.org#{last_request.path}"
    RDF::Graph.new(base_uri) do |graph|
      RDF::Reader::for(:rdfa).new(last_response.body, :base_uri => base_uri) do |reader|
        reader.each_statement do |statement|
          graph << statement
        end
      end
    end
  end
end
