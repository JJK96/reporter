\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{report}[2021/06/12 report]
\LoadClass[11pt]{article}

%Table styles
\RequirePackage[table]{xcolor}
\RequirePackage{_packages/tablestyles/tablestyles}
\RequirePackage{tabularx}
\RequirePackage{tabulary} % For automatically fitting column widths based on content

%Fix spacing with URL and paths
\usepackage[obeyspaces,hyphens]{url}
%Clicakble links
\RequirePackage{hyperref}

% Graphbox for vertically centering image in table, provides align option to \includegraphics
\RequirePackage{graphbox} %loads graphicx package

\RequirePackage{tikz}

%For tpage toggle
\RequirePackage{etoolbox}

% Set font
\RequirePackage{fontspec}
\setmainfont{Calibri}

%If statements
\RequirePackage{ifthen}

%More space between paragraphs
\RequirePackage{parskip}

\input{theme.tex}

%List and crossreferences of tools
\RequirePackage{_packages/tools/tools}
\input{tools.tex}

%Make underscore behave normal
\catcode`\_11

% Labels with custom text (used for referencing issues with the text of their issue number)
% From: https://tex.stackexchange.com/questions/438876/how-to-cross-reference-text-with-a-custom-label-reference-text
\newcommand{\mylabeltext}[3][]{%
    \@bsphack%
    \csname phantomsection\endcsname% in case hyperref is used
    \def\tst{#1}%
    \def\labelmarkup{\emph}% How to markup the label itself
    %\def\refmarkup{\labelmarkup}% How to markup the reference
    \def\refmarkup{}%
    \ifx\tst\empty\def\@currentlabel{\refmarkup{#2}}{\label{#3}}%
    \else\def\@currentlabel{\refmarkup{#1}}{\label{#3}}\fi%
    \@esphack%
    %\labelmarkup{#2}% visible printed text.
    \message{Label `#3` defined.}
}

%Listings
\RequirePackage{listings}
\RequirePackage{realboxes} % For \Colorbox which works with verbatim inside
\RequirePackage{mdframed} %For background and frame
\RequirePackage{luacolor,lua-ul}% LuaLaTeX based improved color and underlining/highlighting support

% By default, lua-ul's \highLight has to be used as \highLight[color]{text}, 
% but moredelim=** needs a command which gets used as {\highLight[color] text}
% Therefore we define \highLightSwitch as such a variant
\DeclareDocumentCommand\highLightSwitch{m}{%
  \luaul@setcolor{#1}%
  \@highLight
}

% Define a new language with `literate` set to almost all characters. This allows line breaks on these characters. Otherwise long words would overflow.
% From https://tex.stackexchange.com/questions/33459/how-to-deal-with-very-long-lines-that-do-not-contain-spaces/442402#442402
\def\@tempA#1#2\@end{%
    \@tempA@{#1}%
    \ifx\relax#2\relax
    \else
        \@tempA#2\@end
    \fi
}
\def\@tempA@#1{{\noexpand#1}{{\char`\noexpand#1 \allowbreak}}1 }
\edef\@tempB{\noexpand\lstdefinelanguage{logfile}{%
    columns=fixed,%
    keepspaces=true,%
    breaklines=true,%
    literate=\@tempA 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!()*+,-./:;<=>?@[]_|`^"'\&\\\~\#\%\@end
}}
\@tempB

% variables
\newcommand{\VAR}[1]{#1}
\newcommand{\BLOCK}[1]{#1}

% Listing settings
\lstset{
    basicstyle={\listingstyle},
    breakatwhitespace=false,
    language=logfile,
    breaklines=true,
    keepspaces=true,
    xleftmargin=-5pt,
    xrightmargin=-5pt,
    belowskip=0pt,
    moredelim=**[is][\highLightSwitch{highlight}]{$$\{\{}{\}\}$$}, % Tell listings about our markers
                                                                % ** indicate that it should be combined with other styles.
    moredelim=**[is][\color{highlight1}]{$$*\{\{}{\}\}*$$}, % Tell listings about our markers
                                                                % ** indicate that it should be combined with other styles.
}
\lstnewenvironment{code}{
    % To add the right spacing with previous paragraph
    \vspace{\parskip}
    \mdframed[backgroundcolor=codebg,linecolor=black,linewidth=1pt]
}{
    \endmdframed
}
% Inline code
\newcommand\codeinline{\lstinline[basicstyle={\lstinlinestyle}]}

% Table span multiple pages
\RequirePackage{longtable}
% Span full text width
\setlength\LTleft{0pt}
\setlength\LTright{0pt}

% Define variables 
\newcommand{\companyname}[1]{\newcommand{\@companyname}{#1}}
\newcommand{\version}[1]{\newcommand{\@version}{#1}}

% Remove indentation at start of paragraph
\setlength\parindent{0pt}

% Reduce space between items
\RequirePackage{enumitem}
\setlist{noitemsep}

%Determine whether the title page is active (for background)
\newtoggle{tpage}

% Report date overridable by \reportdate
\def\twodigits#1{\ifnum#1<10 0\fi\the#1}
\newcommand{\@reportdate}{\leavevmode\hbox{\twodigits\day-\twodigits\month-\the\year}}
\newcommand{\reportdate}[1]{\renewcommand{\@reportdate}{#1}}

\renewcommand{\contentsname}{\VAR{table_of_contents}}

% Issue severity headers
\newcommand\critical{\subsection{\VAR{risk_sections.critical}}\def\issueseverity{critical}}
\newcommand\high{\subsection{\VAR{risk_sections.high}}\def\issueseverity{high}}
\newcommand\medium{\subsection{\VAR{risk_sections.medium}}\def\issueseverity{medium}}
\newcommand\low{\subsection{\VAR{risk_sections.low}}\def\issueseverity{low}}
\newcommand\none{\subsection{\VAR{risk_sections.none}}\def\issueseverity{none}}

\newcommand{\@cvssscoretext}{\VAR{text.cvss_score}}

% Colored issue header with white text for critical
\newcommand{\issueheader}{
    \rowcolor{\issueseverity}
    \ifthenelse{\equal{\issueseverity}{critical}}{%
        \textcolor{white}{\@cvssscoretext} & \textcolor{white}{\@cvss~-~\issueseverity}
    }{%
        \@cvssscoretext & \@cvss
    }
    \tabularnewline
}

% Table newline with hline
\newcommand{\tnl}{
    \\ \hline
}

%Issue counter
\newcounter{issue}

%Issue variables
\newcommand{\cvss}[1]{\newcommand\@cvss{#1}}
\newcommand{\descriptionfield}[1]{\newcommand\@description{#1}}
\newcommand{\solution}[1]{\newcommand\@solution{#1}}
\newcommand{\location}[1]{\newcommand\@location{#1}}
\newcommand{\cvssvector}[1]{\newcommand\@cvssvector{#1}}

\input{issue_env.tex}

\newcommand{\findingtablebox}[1]{
    \parbox[c][][c]{\textwidth}{
        \vspace{.5\baselineskip}
        #1
        \vspace{-.5\baselineskip}
    }
}

\input{findingtable.tex}

\newenvironment{evidence}[1]{
    \BLOCK{ if config.show_locations != 'False'}
        \par%
        \emergencystretch 3em% Avoid going over the end of the line
        \subparagraph{#1}%
        \par%
    \BLOCK{ else }
        \par%
    \BLOCK{ endif }
}{}

\newcommand{\image}[2][1]{\includegraphics[width=#1\textwidth]{images/#2}}
\newcommand{\signature}[1]{\includegraphics[align=t,width=3cm]{#1}}

% Table with amount of findings per risk level
\newcommand\numfindings[1]{\newcommand{\@numfindings}{#1}}
\newcommand\numcritical[1]{\newcommand{\@numcritical}{#1}}
\newcommand\numhigh[1]{\newcommand{\@numhigh}{#1}}
\newcommand\nummedium[1]{\newcommand{\@nummedium}{#1}}
\newcommand\numlow[1]{\newcommand{\@numlow}{#1}}
\newcommand\numnone[1]{\newcommand{\@numnone}{#1}}

\newcommand{\conclusion}[1]{\newcommand{\@conclusion}{#1}}
