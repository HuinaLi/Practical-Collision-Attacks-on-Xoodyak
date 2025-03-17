# SAC25-Practical-Collision-Attacks-on-Reduced-Round-Xoodyak-Hash-Mode
The source codes and results are used to help verify the results in our paper.


\xoodyak is a finalist of the NIST lightweight cryptography competition, offering both keyed and hash modes. After several years of cryptanalysis, the largest number of \xoodyak hash rounds for which actual collisions  was still in vacancy. 
To the best of our knowledge, one of the most powerful collision attacks on hash functions based on  sponge construction is  the differential-based attacks using the S-box linearization technique proposed by Qiao \etal (EUROCRYPT 2017).
However, the linearization technique requires  a large number of degrees of freedom, making it challenging to apply to \xoodyak with a small outer part. On the other hand, the constraint-input and constraint-output imposed on the differential trail of \xoodoo permutation make the exhaustive search for such high-probability differential trails in collision attacks extremely costly.


 In this paper, we present critical observations regarding \xoodoo round function, particularly focusing on its unique  $\theta$ and $\chi$ operation. These properties can be leveraged to manually design specific differential trails for the \xoodoo permutation, referred to as \textit{loop} differential trails. To efficiently find practical collisions for up to 3 rounds, we develop a SAT model based on these \textit{loop} trails.  Finally, we present the first practical collision on 2 rounds and a practical semi-free-start collision on 3 rounds of \xoodyak hash mode. Besides,  we improve Dong \etal's (CRYPTO 2024) collision attack on 3-round \xoodyak-\hash from $2^{125.23}$ to $2^{100.93}$ using several linearization strategies.
 Since we focus on the analysis on collisions during the message absorbing phase of the hash modes, our results are applicable to both \xoodyak-\hash and \xoodyak-\xof.
